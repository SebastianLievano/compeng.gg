import courses.models as db
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from courses.teams.schemas import (
    JoinTeamRequestSerializer,
    LeaveTeamRequestSerializer, 
    ManageTeamMemberRequestSerializer,
    DeleteTeamRequestSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from uuid import UUID

from dataclasses import dataclass

@dataclass
class TeamEnrollmentData:
    team: db.Team
    enrollment: db.Enrollment


def get_student_enrollment_for_team(team_id: UUID, user_id: int) -> TeamEnrollmentData:
    try:
        team = db.Team.objects.get(
            id=team_id,
        )
    except db.Team.DoesNotExist:
        raise ValidationError()
    
    course_slug = team.offering.course.slug
    
    try:
        offering = db.Offering.objects.get(
            course__slug=course_slug,
            active=True
        )
    except db.Offering.DoesNotExist:
        raise ValidationError()

    try:
        role = db.Role.objects.get(
            kind=db.Role.Kind.STUDENT,
            offering=offering,
        )
    except db.Role.DoesNotExist:
        raise ValidationError()
    
    try:
        enrollment = db.Enrollment.objects.get(
            role=role,
            user_id=user_id,
        )
    except db.Enrollment.DoesNotExist:
        raise ValidationError()
    
    return TeamEnrollmentData(
        team=team,
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
        enrollment = team_enrollment_data.enrollment
        
        if db.TeamMember.objects.filter(enrollment=enrollment).count() > 0:
            raise ValidationError()

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
    from courses.models import TeamMember
    serializer = ManageTeamMemberRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        team_id = serializer.validated_data.get('team_id')
        joiner_name = serializer.validated_data.get('joiner_name')
        approved = serializer.validated_data.get('approved')
        request_id = request.user.id
        
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
        
        if leader == None or approvedJoiner == None:
            raise ValidationError()
        
        if approved:
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
            raise ValidationError()
        
        if team_member.membership_type != db.TeamMember.MembershipType.LEADER:
            raise ValidationError()
  
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
            raise ValidationError()
        
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
    from courses.models import Team, Offering
    user = request.user
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
    from courses.teams.schemas import CreateTeamRequestSerializer
    from courses.models import Offering
    serializer = CreateTeamRequestSerializer(data=request.data)

    if serializer.is_valid():
        user_id = request.user.id
        team_name = serializer.validated_data.get('team_name')
        course_slug = serializer.validated_data.get('course_slug')

        try:
            offering = Offering.objects.get(course__slug=course_slug)
        except Offering.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

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

        team = db.Team.objects.create(
            name=team_name,
            offering=offering,
        )

        db.TeamMember.objects.create(
            team=team,
            enrollment=enrollment,
            membership_type=db.TeamMember.MembershipType.LEADER,
        )

        return Response({'id': team.id, 'name': team.name}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)