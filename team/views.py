from django.shortcuts import render
from rest_framework import viewsets
from core import utility
from rest_framework.response import Response

from core.utility import remove_path
from .models import Team, TeamMember
from team.serializers import TeamMemberSerializer, TeamSerializer
from core.views import BaseDynamicModelViewSet
from rest_framework.decorators import action
from rest_framework import status

class TeamViewSet(BaseDynamicModelViewSet):
    serializer_class = TeamSerializer
    queryset = Team.objects.all()
    http_method_names = ['get','post', 'put', 'patch','delete']

    @staticmethod
    def _delete_image(image):
        if image.storage:
            image.storage.delete(image.name)
        else:
            remove_path(image.path)

    # @action(methods=['post'], url_path='upload_image', detail=True)
    # def upload_image(self, request, pk):
    #     try:
    #         team = Team.objects.get(pk=pk)

    #         # Delete the previous image file if it exist
    #         if team.team_image:
    #             remove_path(team.team_image.path)

    #         if "image" in request.data:
    #             file = request.data["image"]
    #             team.team_image = utility.resize_image(
    #                 file, max_size_kb=300, max_dimension_pixel=1200
    #             )
    #             team.save()

    #     except Team.DoesNotExist:
    #         return Response(status=status.HTTP_400_BAD_REQUEST)

    #     serializer = self.get_serializer(team)
    #     return Response(serializer.data)
    
    # @action(methods=['post'], url_path='delete_image', detail=True)
    # def delete_image(self, request, pk):
    #     try:
    #         team = Team.objects.get(pk=pk)

    #         # Delete the previous image file if it exist
    #         if team.team_image:
    #             self._delete_image(team.team_image)
    #             remove_path(team.team_image.path)
    #             team.team_image = None
    #             team.save()

    #     except Team.DoesNotExist:
    #         return Response(status=status.HTTP_400_BAD_REQUEST)

    #     serializer = self.get_serializer(team)
    #     return Response(serializer.data)

    @action(methods=['post'], url_path='edit_team', detail=True)
    def edit_team(self, request,pk):
        try:
            team = Team.objects.get(pk=pk)

            #Update the name
            if "name" in request.data:
                team.name = request.data["name"]

            # Delete image if requested
            if request.data.get("delete_image") and team.team_image:
                self._delete_image(team.team_image)
                team.team_image = None

            #New image upload
            if "image" in request.data and request.data["image"]:
                file = request.data["image"]

                #Delete the previous image file if exist
                if team.team_image:
                    self._delete_image(team.team_image)
                    remove_path(team.team_image.path)
                    team.team_image = None

                    
                team.team_image = utility.resize_image(
                    file, max_size_kb=300, max_dimension_pixel=1200)
                
            team.save()

        except Team.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(team)
        return Response(serializer.data)

class TeamMemberViewSet(BaseDynamicModelViewSet):
    serializer_class = TeamMemberSerializer
    queryset = TeamMember.objects.all()
    http_method_names = ['get','post', 'put', 'patch','delete']

