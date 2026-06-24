import csv
import codecs
from datetime import datetime
import json
import re

from core.utility import csv_text
from core.models import Tenant
from iteration.models import Iteration
from task.models import Task
from .models import Story
from project.models import Project
from team.models import Team, TeamMember
from django.db.models import Q

def read_csv(input_csv_file):
    # Define the columns to extract
    columns_to_extract = ["\ufeffID", "Work Item Type", "Title 2", "Title 3", "Tags", "Description", "Acceptance Criteria"]

    output_text_file = 'story/output.txt' 

    # Define the regex pattern to remove HTML tags and entities
    CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

    try:
        with open(input_csv_file, 'r', newline='', encoding='utf-8') as csv_file, open(output_text_file, 'w', encoding='utf-8') as text_file:
            csv_reader = csv.DictReader(csv_file)

            for row in csv_reader:
                work_item_type = row["Work Item Type"].strip().lower()
                if work_item_type != "epic" and work_item_type != "task":
                    # Iterate through the columns to extract
                    for column in columns_to_extract:
                        try:
                            value = row[column].strip()
                            if column in ["Description", "Acceptance Criteria"]:
                                cleaned_text = re.sub(CLEANR, '', value)
                                text_file.write(f"{column}: {cleaned_text}\t \n")
                            else:
                                text_file.write(f"{column}: {value}\t \n")
                        except Exception as e:
                            # Handle exceptions, e.g., for problematic content
                            text_file.write(f"Error in {column}: {str(e)}\t")

                    # Add an empty line between records
                    text_file.write("\n")
        print("file created successfully")
        return output_text_file  # Return the name of the created text file
    except Exception as e:
        print("Error: " + str(e))
        return str(e)  # Error message

def import_story_csv_file(csv_file, tenant: Tenant):
    TITLE_COL = 0
    DESCRIPTION_COL = 1
    ACCEPTANCE_CRITERIA_COL = 2

    count = 0
    story_created_count = 0
    option_reader = csv.reader(codecs.iterdecode(csv_file, 'utf-8'), delimiter=',')
    next(option_reader)  # Skip header

    data_json = dict()
    note_data_json = dict()

    prev_story_name = None
    current_story = None

    for row in option_reader:
        if any(field.strip() for field in row):
            # Parse CSV columns
            title = csv_text(row, TITLE_COL).strip()

            description = ''
            acceptance_criteria = ''

            if csv_text(row, DESCRIPTION_COL):
                description = '<p><span style="background-color:hsl(120, 75%, 60%);"><strong><u>Description:</u></strong></span></p>' + csv_text(row, DESCRIPTION_COL).strip() + '<br><br>' 

            if csv_text(row, ACCEPTANCE_CRITERIA_COL):
                acceptance_criteria = '<p><span style="background-color:hsl(120, 75%, 60%);"><strong><u>Acceptance Criteria:</u></strong></span></p>' + csv_text(row, ACCEPTANCE_CRITERIA_COL).strip()
                
            # Combine the title, description, and acceptance criteria into story.description
            story_description =  description + acceptance_criteria

            # Check if the team exists, create if not
            team, team_created = Team.objects.get_or_create(
                name='Tech Team', tenant=tenant
            )

            # Check if the project exists, create if not
            project, project_created = Project.objects.get_or_create(
                name='Sunway', team=team, tenant=tenant
            )
            
            if story_description and story_description != prev_story_name:
                if current_story is not None:
                    current_story.data_json = json.dumps(data_json)
                    current_story.note_data_json = json.dumps(note_data_json)
                    current_story.save()
                    data_json = dict()

                story, story_created = Story.objects.get_or_create(
                    name = title,
                    description=story_description,
                    project=project,
                    team=team,
                    is_active=True,
                    tenant=tenant
                )

                current_story = story

                if story_created:
                    data_json = dict()
                    note_data_json = dict()
                    story_created_count += 1

                prev_story_name = story_description

        count += 1

    if current_story is not None:
        current_story.data_json = json.dumps(data_json)
        current_story.note_data_json = json.dumps(note_data_json)
        current_story.save()

    return story_created_count

def get_incomplete_story(user, iteration):
    if not iteration: 
        team_member = TeamMember.objects.filter(user=user, is_active=True).first()

        if not team_member:
            return []

        team = team_member.team
        iteration = Iteration.objects.filter(team=team, is_active=True).order_by('-id').first()

    incomplete_tasks = Task.objects.filter(
        user=user,
        status__in=[Task.STATUS_DO, Task.STATUS_DOING, Task.STATUS_PENDING]
    )
    
    story_ids = incomplete_tasks.values_list('story__id', flat=True)
    incomplete_stories = Story.objects.filter(id__in=story_ids)

    return incomplete_stories

def get_my_task_story(user, iteration):
    if not iteration: 
        team_member = TeamMember.objects.filter(user=user, is_active=True).first()

        if not team_member:
            return []

        team = team_member.team
        iteration = Iteration.objects.filter(team=team, is_active=True).order_by('-id').first()

    incomplete_tasks = Task.objects.filter(
        user=user,
        iteration=iteration,
    ) 

    story_ids = incomplete_tasks.values_list('story__id', flat=True)
    incomplete_stories = Story.objects.filter(id__in=story_ids)

    return incomplete_stories

def check_should_celebrate(iteration):    
    stories = Story.objects.filter(
        iteration=iteration,
        is_active=True
    ).exclude(status=Story.STATUS_COMPLETED)
    
    should_celebrate = stories.count() == 0
    
    return {
        'should_celebrate': should_celebrate,
    }