import courses.models as db
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from courses.teams.schemas import JoinTeamRequestSerializer, LeaveTeamRequestSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def join_team(request):
    serializer = JoinTeamRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        enrollment_id = serializer.validated_data.get('enrollment_id')
        team_id = serializer.validated_data.get('team_id')
        user_id = request.user.id
        
        try:
            enrollment = db.Enrollment.objects.get(id=enrollment_id, user_id=user_id)
        except db.Enrollment.DoesNotExist:
            # TODO: raise error if enrollment does not exist
            raise ValidationError("DDD")
        
        offering_id = enrollment.role.offering.id 
        
        if enrollment.team is not None:
            # TODO: raise error if already in team
            raise ValidationError("ddd")
        
        try:
            team = db.Team.objects.get(id=team_id, offering_id=offering_id)
        except db.Team.DoesNotExist:
            # TODO: raise error if team does not exist
            pass
        
        enrollment.team = team
        enrollment.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # If validation fails, return error response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def leave_team(request):
    serializer = LeaveTeamRequestSerializer(data=request.data)

    if serializer.is_valid():
        enrollment_id = serializer.validated_data.get('enrollment_id')
        team_id = serializer.validated_data.get('team_id')
        user_id = request.user.id
        
        try:
            enrollment = db.Enrollment.objects.get(id=enrollment_id, user_id=user_id)
        except db.Enrollment.DoesNotExist:
            # TODO: raise error if enrollment does not exist
            raise ValidationError("DDD")
        
        if enrollment.team is None:
            # TODO: raise error if already in team
            raise ValidationError("ddd")
        
        if enrollment.team.id != team_id:
            raise ValidationError("ddd")
        
        enrollment.team = None
        enrollment.save()
    
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # If validation fails, return error response
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
        for enrollment in team.members.all():
            members.append({
                'id': enrollment.user.id,
                'name': enrollment.user.username,
            })
        
        data.append({
            'id': team.id,
            'name': team.name,
            'members': members,
        })
    
    return Response(data)
