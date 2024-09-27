from rest_framework import serializers

class JoinTeamRequestSerializer(serializers.Serializer):
        team_id = serializers.UUIDField(required=True)
        enrollment_id = serializers.UUIDField(required=True)
    
class LeaveTeamRequestSerializer(serializers.Serializer):
        team_id = serializers.UUIDField(required=True)
        enrollment_id = serializers.UUIDField(required=True)