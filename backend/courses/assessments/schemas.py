from rest_framework import serializers
import courses.models as db
from typing import (
    List,
    Dict,
    Any,
    Optional
)


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    question_type = serializers.CharField(default='MULTIPLE_CHOICE', read_only=True)
    selected_answer_index = serializers.SerializerMethodField()

    class Meta:
        model = db.MultipleChoiceQuestion
        fields = ['order', 'prompt', 'question_type', 'points', 'options', 'selected_answer_index']

    def get_selected_answer_index(self, multiple_choice_question: db.MultipleChoiceQuestion) -> int:
        if (answer := multiple_choice_question.answers.first()) is None:
            return None
        
        return answer.selected_answer_index


class CheckboxQuestionSerializer(serializers.ModelSerializer):
    question_type = serializers.CharField(default='CHECKBOX', read_only=True)
    selected_answer_indices = serializers.SerializerMethodField()

    class Meta:
        model = db.CheckboxQuestion
        fields = ['order', 'prompt', 'question_type', 'points', 'options', 'selected_answer_indices']

    def get_selected_answer_indices(self, checkbox_question: db.CheckboxQuestion) -> List[int]:
        if (answer := checkbox_question.answers.first()) is None:
            return None
        
        return answer.selected_answer_indices


class WrittenResponseQuestionSerializer(serializers.ModelSerializer):
    question_type = serializers.CharField(default='WRITTEN_RESPONSE', read_only=True)
    response = serializers.SerializerMethodField()

    class Meta:
        model = db.WrittenResponseQuestion
        fields = ['order', 'prompt', 'question_type', 'points', 'max_length', 'question_type', 'response']

    def get_response(self, written_response_question: db.WrittenResponseQuestion) -> str:
        if (answer := written_response_question.answers.first()) is None:
            return None
        
        return answer.response


class CodingQuestionSerializer(serializers.ModelSerializer):
    question_type = serializers.CharField(default='CODING', read_only=True)
    solution = serializers.SerializerMethodField()

    class Meta:
        model = db.CodingQuestion
        fields = ['order', 'prompt', 'points', 'programming_language', 'question_type', 'starter_code', 'solution']

    def get_solution(self, coding_question: db.CodingQuestion) -> str:
        if (answer := coding_question.answers.first()) is None:
            return None
        
        return answer.solution


class AssessmentSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    end_unix_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = db.Assessment
        fields = ['title', 'end_unix_timestamp', 'questions']

    def get_questions(self, assessment: db.Assessment) -> List[Dict[str, Any]]:
        checkbox_questions = assessment.checkbox_questions
        multiple_choice_questions = assessment.multiple_choice_questions
        written_response_questions = assessment.written_response_questions
        coding_questions = assessment.coding_questions
       
        serialized_multiple_choice_questions = MultipleChoiceQuestionSerializer(
            multiple_choice_questions,
            many=True,
        ).data

        serialized_checkbox_questions = CheckboxQuestionSerializer(
            checkbox_questions,
            many=True,
        ).data

        serialized_written_response_questions = WrittenResponseQuestionSerializer(
            written_response_questions, 
            many=True,
        ).data

        serialized_coding_questions = CodingQuestionSerializer(
            coding_questions, 
            many=True,
        ).data
        
        all_questions = serialized_multiple_choice_questions + serialized_checkbox_questions + serialized_written_response_questions + serialized_coding_questions

        sorted_questions = sorted(all_questions, key=lambda question: question['order'])
        
        for question in sorted_questions:
            question.pop('order')

        return sorted_questions
    
    def get_end_unix_timestamp(self, assessment: db.Assessment) -> int:
        return int(assessment.ends_at.timestamp())


class AnswerMultipleChoiceQuestionRequestSerializer(serializers.Serializer):
    selected_answer_index = serializers.IntegerField(required=True)
    
    def validate_selected_answer_index(self, selected_answer_index: int) -> int:
        if selected_answer_index < 0:
            raise serializers.ValidationError('The selected answer index must not be negative')
        
        return selected_answer_index
    

class AnswerWrittenResponseQuestionRequestSerializer(serializers.Serializer):
    response = serializers.CharField(required=True)


class AnswerCodingQuestionRequestSerializer(serializers.Serializer):
    solution = serializers.CharField(required=True)


def validate_list_is_set(input_list: Optional[List[int]]) -> Optional[List[int]]:
    if input_list is None:
        return None
    
    if len(input_list) != len(set(input_list)):
        raise serializers.ValidationError('Input list must not contain duplicate values')

    return input_list


class AnswerCheckboxQuestionRequestSerializer(serializers.Serializer):
    selected_answer_indices = serializers.ListField(
        child=serializers.IntegerField(min_value=0),
        required=False,
        validators=[validate_list_is_set],
    )


class CourseAssessmentsListSerializer(serializers.ModelSerializer):
    start_unix_timestamp = serializers.SerializerMethodField()
    end_unix_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = db.Assessment
        fields = [
            'title', 
            'slug',
            'start_unix_timestamp',
            'end_unix_timestamp'
        ]

    def get_start_unix_timestamp(self, assessment: db.Assessment) -> int:
        return int(assessment.starts_at.timestamp())

    def get_end_unix_timestamp(self, assessment: db.Assessment) -> int:
        return int(assessment.ends_at.timestamp())
    

class AllAssessmentsListSerializer(CourseAssessmentsListSerializer):
    course_slug = serializers.CharField(source='offering.course.slug', read_only=True)
    
    class Meta(CourseAssessmentsListSerializer.Meta):
        fields = CourseAssessmentsListSerializer.Meta.fields + ['course_slug']
