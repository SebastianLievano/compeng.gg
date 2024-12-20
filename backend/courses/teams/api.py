import courses.models as db
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from courses.teams.schemas import (
    JoinTeamRequestSerializer,
    LeaveTeamRequestSerializer, 
    ManageTeamMemberRequestSerializer,
    DeleteTeamRequestSerializer,
    CreateTeamRequestSerializer,
    createTeamWithLeaderRequestSerializer,
    CreateTeamSettingsForOfferingRequestSerializer,
    UpdateTeamSettingsForOfferingRequestSerializer,
    removeTeamMemberRequestSerializer,
    addTeamMemberRequestSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from uuid import UUID
from django.utils import timezone
from github_app.utils import create_student_team_and_fork, add_student_to_github_team
from slugify import slugify
from courses.models import Offering, TeamMember, Team
from github_app.utils import create_student_team_and_fork, add_student_to_github_team
from slugify import slugify

from dataclasses import dataclass
from courses.teams.utils import IsInstructorOrTA

@dataclass
class TeamEnrollmentData:
    team: db.Team
    team_settings: db.OfferingTeamsSettings
    enrollment: db.Enrollment

def get_student_enrollment_for_team(team_id: UUID, user_id: int) -> TeamEnrollmentData:
    try:
        team = db.Team.objects.get(
            id=team_id,
        )
    except db.Team.DoesNotExist:
        raise Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    course_slug = team.offering.course.slug
    try:
        offering = db.Offering.objects.get(
            course__slug=course_slug,
            active=True
        )
    except db.Offering.DoesNotExist:
        raise Response({'detail': 'Offering not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        role = db.Role.objects.get(
            kind=db.Role.Kind.STUDENT,
            offering=offering,
        )
    except db.Role.DoesNotExist:
        raise Response({'detail': 'Role not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        enrollment = db.Enrollment.objects.get(
            role=role,
            user_id=user_id,
        )
    except db.Enrollment.DoesNotExist:
        raise Response({'detail': 'Enrollment not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        team_settings = db.OfferingTeamsSettings.objects.get(offering=team.offering)
    except db.OfferingTeamsSettings.DoesNotExist:
        raise Response({'detail': 'Team settings not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    return TeamEnrollmentData(
        team=team,
        team_settings=team_settings,
        enrollment=enrollment,
    )


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def request_to_join_team(request):
    serializer = JoinTeamRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        team_id = serializer.validated_data.get('team_id')
        user_id = request.user.id
        team_enrollment_data = get_student_enrollment_for_team(
            team_id=team_id,
            user_id=user_id,
        )
        team = team_enrollment_data.team
        enrollment = team_enrollment_data.enrollment
        
        # Validate user does not break membership conditions
        if db.TeamMember.objects.filter(enrollment=enrollment).count() > 0:
            raise Response({'detail': 'User is already in a team.'}, status=status.HTTP_400_BAD_REQUEST)
        
        max_team_size = team_enrollment_data.team_settings.max_team_size
        formation_deadline = team_enrollment_data.team_settings.formation_deadline
        if db.TeamMember.objects.filter(team=team).count() >= max_team_size:
            raise Response({'detail': 'Team is full.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if formation_deadline < timezone.now():
            raise Response({'detail': 'Team formation deadline has passed.'}, status=status.HTTP_400_BAD_REQUEST)
            
        db.TeamMember.objects.create(
            team_id=team_id,
            enrollment=enrollment,
            membership_type=db.TeamMember.MembershipType.REQUESTED_TO_JOIN,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def manage_join_team_request(request):
    serializer = ManageTeamMemberRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        team_id = serializer.validated_data.get('team_id')
        joiner_name = serializer.validated_data.get('joiner_name')
        approved = serializer.validated_data.get('approved')
        request_id = request.user.id
        try:
            team = db.Team.objects.get(id=team_id)
        except db.Team.DoesNotExist:
            raise ValidationError()
    
        teamMembers = db.TeamMember.objects.filter(
            team_id=team_id
        )
        
        leader = None
        approvedJoiner = None
        for member in teamMembers:
            if member.membership_type == TeamMember.MembershipType.LEADER:
                if member.enrollment.user.id == request_id:
                    leader = member
                else: #If leader is not person requesting operation, throw error
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
            elif member.membership_type == TeamMember.MembershipType.REQUESTED_TO_JOIN \
                and member.enrollment.user.username == joiner_name:
                    approvedJoiner = member
        
        if leader == None:
            raise Response({'detail': 'Leader not found.'}, status=status.HTTP_404_NOT_FOUND)
        if approvedJoiner == None:
            raise Response({'detail': 'Joiner not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if approved:
            add_student_to_github_team(request.user, team.github_team_slug)
            approvedJoiner.membership_type = db.TeamMember.MembershipType.MEMBER
            approvedJoiner.save()
        else:
            approvedJoiner.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_team(request):
    serializer = DeleteTeamRequestSerializer(data=request.data)

    if serializer.is_valid():
        team_id = serializer.validated_data.get('team_id')
        user_id = request.user.id

        team_enrollment_data = get_student_enrollment_for_team(
            team_id=team_id,
            user_id=user_id,
        )
        enrollment = team_enrollment_data.enrollment
        team = team_enrollment_data.team

        try:
            team_member = db.TeamMember.objects.get(
                team_id=team_id,
                enrollment=enrollment,
            )
        except db.TeamMember.DoesNotExist:
            raise Response({'detail': 'Team member not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if team_member.membership_type != db.TeamMember.MembershipType.LEADER:
            raise Response({'detail': 'Only team leader can delete team.'}, status=status.HTTP_401_UNAUTHORIZED)
  
        team.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def leave_team(request):
    serializer = LeaveTeamRequestSerializer(data=request.data)

    if serializer.is_valid():
        team_id = serializer.validated_data.get('team_id')
        user_id = request.user.id

        team_enrollment_data = get_student_enrollment_for_team(
            team_id=team_id,
            user_id=user_id,
        )
        enrollment = team_enrollment_data.enrollment
        team = team_enrollment_data.team
        
        try:
            team_member = db.TeamMember.objects.get(
                team=team,
                enrollment=enrollment,
            )
        except db.TeamMember.DoesNotExist:
            raise Response({'detail': 'Team member not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        team_empty = False
        
        #Frontend only allows deletion by leader if team is empty
        if team_member.membership_type == db.TeamMember.MembershipType.LEADER:
            team_empty = True
        
        team_member.delete()
        if team_empty:
            team.delete()
    
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def teams(request, slug):
    try:
        offering = Offering.objects.get(course__slug=slug)
    except Offering.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    data = []
    for team in Team.objects.filter(offering=offering):
        members = []
        for teamMember in team.members.all():
            members.append({
                'role': teamMember.membership_type,
                'name': teamMember.enrollment.user.username,
            })
        
        data.append({
            'id': team.id,
            'name': team.name,
            'members': members,
        })
    
    return Response(data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_team(request):
    serializer = CreateTeamRequestSerializer(data=request.data)

    if serializer.is_valid():
        # Validations
        team_name = serializer.validated_data.get('team_name')
        course_slug = serializer.validated_data.get('course_slug')
        try:
            offering = Offering.objects.get(course__slug=course_slug)
        except Offering.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            team_settings = db.OfferingTeamsSettings.objects.get(offering=offering)
        except db.OfferingTeamsSettings.DoesNotExist:
            raise Response({'detail': 'Team settings not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if team_settings.formation_deadline < timezone.now():
            raise Response({'detail': 'Team formation deadline has passed.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            role = db.Role.objects.get(
                kind=db.Role.Kind.STUDENT,
                offering=offering,
            )
        except db.Role.DoesNotExist:
            return Response({'detail': 'Role not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            enrollment = db.Enrollment.objects.get(
                role=role,
                user=request.user,
            )
        except db.Enrollment.DoesNotExist:
            return Response({'detail': 'Enrollment not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Create team models
        create_student_team_and_fork(offering, team_name, request.user)
        team = db.Team.objects.create(
            name=team_name,
            offering=offering,
            created_at=timezone.now(),
            github_team_slug=slugify(team_name)
        )
        db.TeamMember.objects.create(
            team=team,
            enrollment=enrollment,
            membership_type=db.TeamMember.MembershipType.LEADER,
        )

        return Response({'id': team.id, 'name': team.name}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_team_settings_for_offering(request, slug):
    try:
        offering = Offering.objects.get(course__slug=slug)
        team_settings = db.OfferingTeamsSettings.objects.get(offering=offering)
    except (Offering.DoesNotExist, db.OfferingTeamsSettings.DoesNotExist) as e:
        return Response(e, status=status.HTTP_404_NOT_FOUND)
    
    return Response(team_settings)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_team_settings_for_offering(request):
    serializer = CreateTeamSettingsForOfferingRequestSerializer(data=request.data)

    if serializer.is_valid():
        offering_id = serializer.validated_data.get('offering_id')

        try:
            offering = db.Offering.objects.get(id=offering_id)
        except db.Offering.DoesNotExist:
            return Response({'detail': 'Offering not found.'}, status=status.HTTP_404_NOT_FOUND)

        team = db.OfferingTeamsSettings.objects.create(
            offering=offering,
            max_team_size = serializer.validated_data.get('max_team_size'),
            formation_deadline = serializer.validated_data.get('formation_deadline'),
            show_group_members = serializer.validated_data.get('show_group_members'),
            allow_custom_names = serializer.validated_data.get('allow_custom_names'),
        )

        return Response({'id': team.id, 'name': team.name}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_team_settings_for_offering(request):
    serializer = UpdateTeamSettingsForOfferingRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        offering_id = serializer.validated_data.get('offering_id')
        try:
            offering = db.Offering.objects.get(id=offering_id)
        except db.Offering.DoesNotExist:
            return Response({'detail': 'Offering not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            offering_team_settings = db.OfferingTeamsSettings.objects.get(offering=offering)
        except db.Offering.DoesNotExist:
            return Response({'detail': 'Team setting not found.'}, status=status.HTTP_404_NOT_FOUND)

        max_team_size = serializer.validated_data.get('max_team_size')
        formation_deadline = serializer.validated_data.get('formation_deadline')
        show_group_members = serializer.validated_data.get('show_group_members')
        allow_custom_names = serializer.validated_data.get('allow_custom_names')

        offering_team_settings.max_team_size = max_team_size
        offering_team_settings.formation_deadline = formation_deadline
        offering_team_settings.show_group_members = show_group_members
        offering_team_settings.allow_custom_names = allow_custom_names
        offering_team_settings.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_team_settings_for_offering(request, slug):
    try:
        offering = Offering.objects.get(course__slug=slug)
        team_settings = db.OfferingTeamsSettings.objects.get(offering=offering)
    except (Offering.DoesNotExist, db.OfferingTeamsSettings.DoesNotExist) as e:
        return Response(e, status=status.HTTP_404_NOT_FOUND)
    
    return Response(team_settings)

@api_view(['POST'])
@permission_classes([IsInstructorOrTA])
def add_member_to_team(request):
    serializer = addTeamMemberRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        team_id = serializer.validated_data.get('team_id')
        member_id = serializer.validated_data.get('member_id')
        
        try:
            team = db.Team.objects.get(id=team_id)
        except db.Team.DoesNotExist:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            member = db.TeamMember.objects.get(id=member_id)
        except db.TeamMember.DoesNotExist:
            return Response({'detail': 'Member not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        member.team = team
        member.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['DELETE'])
@permission_classes([IsInstructorOrTA])
def remove_member_from_team(request):
    serializer = removeTeamMemberRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        team_id = serializer.validated_data.get('team_id')
        member_id = serializer.validated_data.get('member_id')
        
        try:
            team = db.Team.objects.get(id=team_id)
        except db.Team.DoesNotExist:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            member = db.TeamMember.objects.get(id=member_id)
        except db.TeamMember.DoesNotExist:
            return Response({'detail': 'Member not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        member.delete()
        
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['DELETE'])
@permission_classes([IsInstructorOrTA])
def delete_team_as_admin(request):
    serializer = DeleteTeamRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        team_id = serializer.validated_data.get('team_id')
        
        try:
            team = db.Team.objects.get(id=team_id)
        except db.Team.DoesNotExist:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        team.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsInstructorOrTA])
def create_team_with_leader(request):
    serializer = createTeamWithLeaderRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        team_name = serializer.validated_data.get('team_name')
        course_slug = serializer.validated_data.get('course_slug')
        leader_name = serializer.validated_data.get('leader_name')
        
        try:
            offering = Offering.objects.get(course__slug=course_slug)
        except Offering.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        try:
            team_settings = db.OfferingTeamsSettings.objects.get(offering=offering)
        except db.OfferingTeamsSettings.DoesNotExist:
            raise Response({'detail': 'Team settings not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            role = db.Role.objects.get(
                kind=db.Role.Kind.STUDENT,
                offering=offering,
            )
        except db.Role.DoesNotExist:
            return Response({'detail': 'Role not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            leader = db.Enrollment.objects.get(
                role=role,
                user__username=leader_name,
            )
        except db.Enrollment.DoesNotExist:
            return Response({'detail': 'Leader not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        team = db.Team.objects.create(
            name=team_name,
            offering=offering,
        )
        
        db.TeamMember.objects.create(
            team=team,
            enrollment=leader,
            membership_type=db.TeamMember.MembershipType.LEADER,
        )
        
        return Response({'id': team.id, 'name': team.name}, status=status.HTTP_201_CREATED)
    
    return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_team_status(request, slug):
    try:
        offering = db.Offering.objects.get(course__slug=slug)
    except db.Offering.DoesNotExist:
        return Response({'detail': 'Offering not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        role = db.Role.objects.get(
            kind=db.Role.Kind.STUDENT,
            offering=offering,
        )
    except db.Role.DoesNotExist:
        return Response({'detail': 'Role not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        enrollment = db.Enrollment.objects.get(
            role=role,
            user=request.user,
        )
    except db.Enrollment.DoesNotExist:
        return Response({'detail': 'Enrollment not found.'}, status=status.HTTP_404_NOT_FOUND)

    team_member = TeamMember.objects.filter(enrollment=enrollment).first()
    if team_member:
        team_data = {
            'team_id': team_member.team.id,
            'team_name': team_member.team.name,
            'membership_type': team_member.membership_type,
        }
    else:
        team_data = None

    return Response({'user_id': request.user.id, 'team': team_data})