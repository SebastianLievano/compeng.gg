from rest_framework import serializers
import courses.models as db
from typing import List, Dict, Any, Optional


DEFAULT_QUIZ_QUESTION_FIELDS = [
    "order",
    "prompt",
    "render_prompt_as_latex",
    "points",
    "id",
    "question_type",
    "images",
]


class BaseQuestionSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    def get_images(self, question) -> List[dict]:
        """Retrieve question images sorted by 'order' field."""
        res = []
        print("images")
        for image in question.images.all().order_by("order"):
            res.append({"caption": image.caption, "id": image.id, "order": image.order})
        print(res)
        return res


class MultipleChoiceQuestionSerializer(BaseQuestionSerializer):
    question_type = serializers.CharField(default="MULTIPLE_CHOICE", read_only=True)
    selected_answer_index = serializers.SerializerMethodField()

    class Meta:
        model = db.MultipleChoiceQuestion
        fields = DEFAULT_QUIZ_QUESTION_FIELDS + [
            "options",
            "selected_answer_index",
        ]

    def get_selected_answer_index(
        self, multiple_choice_question: db.MultipleChoiceQuestion
    ) -> Optional[int]:
        if (answer := multiple_choice_question.answers.first()) is None:
            return None

        return answer.selected_answer_index


class CheckboxQuestionSerializer(BaseQuestionSerializer):
    question_type = serializers.CharField(default="CHECKBOX", read_only=True)
    selected_answer_indices = serializers.SerializerMethodField()

    class Meta:
        model = db.CheckboxQuestion
        fields = DEFAULT_QUIZ_QUESTION_FIELDS + [
            "options",
            "selected_answer_indices",
        ]

    def get_selected_answer_indices(
        self, checkbox_question: db.CheckboxQuestion
    ) -> Optional[List[int]]:
        if (answer := checkbox_question.answers.first()) is None:
            return None

        return answer.selected_answer_indices


class WrittenResponseQuestionSerializer(BaseQuestionSerializer):
    question_type = serializers.CharField(default="WRITTEN_RESPONSE", read_only=True)
    response = serializers.SerializerMethodField()

    class Meta:
        model = db.WrittenResponseQuestion
        fields = DEFAULT_QUIZ_QUESTION_FIELDS + [
            "max_length",
            "response",
        ]

    def get_response(
        self, written_response_question: db.WrittenResponseQuestion
    ) -> Optional[str]:
        if (answer := written_response_question.answers.first()) is None:
            return None

        return answer.response


class CodingQuestionSerializer(BaseQuestionSerializer):
    question_type = serializers.CharField(default="CODING", read_only=True)
    solution = serializers.SerializerMethodField()

    class Meta:
        model = db.CodingQuestion
        fields = DEFAULT_QUIZ_QUESTION_FIELDS + [
            "starter_code",
            "programming_language",
            "solution",
        ]

    def get_solution(self, coding_question: db.CodingQuestion) -> Optional[str]:
        if (answer := coding_question.answers.first()) is None:
            return None

        return answer.solution


class QuizSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    end_unix_timestamp = serializers.SerializerMethodField()
    start_unix_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = db.Quiz
        fields = [
            "title",
            "end_unix_timestamp",
            "start_unix_timestamp",
            "questions",
        ]

    def get_questions(self, quiz: db.Quiz) -> List[Dict[str, Any]]:
        checkbox_questions = quiz.checkbox_questions
        multiple_choice_questions = quiz.multiple_choice_questions
        written_response_questions = quiz.written_response_questions
        coding_questions = quiz.coding_questions

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

        all_questions = (
            serialized_multiple_choice_questions
            + serialized_checkbox_questions
            + serialized_written_response_questions
            + serialized_coding_questions
        )

        sorted_questions = sorted(all_questions, key=lambda question: question["order"])

        for question in sorted_questions:
            question.pop("order")

        return sorted_questions

    def get_end_unix_timestamp(self, quiz: db.Quiz) -> int:
        return int(quiz.ends_at.timestamp())

    def get_start_unix_timestamp(self, quiz: db.Quiz) -> int:
        return int(quiz.starts_at.timestamp())


class AnswerMultipleChoiceQuestionRequestSerializer(serializers.Serializer):
    selected_answer_index = serializers.IntegerField(required=True)

    def validate_selected_answer_index(self, selected_answer_index: int) -> int:
        if selected_answer_index < 0:
            raise serializers.ValidationError(
                "The selected answer index must not be negative"
            )

        return selected_answer_index


class AnswerWrittenResponseQuestionRequestSerializer(serializers.Serializer):
    response = serializers.CharField(required=True)


class AnswerCodingQuestionRequestSerializer(serializers.Serializer):
    solution = serializers.CharField(required=True)


def validate_list_is_set(input_list: Optional[List[int]]) -> Optional[List[int]]:
    if input_list is None:
        return None

    if len(input_list) != len(set(input_list)):
        raise serializers.ValidationError(
            "Input list must not contain duplicate values"
        )

    return input_list


class AnswerCheckboxQuestionRequestSerializer(serializers.Serializer):
    selected_answer_indices = serializers.ListField(
        child=serializers.IntegerField(min_value=0),
        required=False,
        validators=[validate_list_is_set],
    )


class CourseQuizzesListSerializer(serializers.ModelSerializer):
    start_unix_timestamp = serializers.SerializerMethodField()
    end_unix_timestamp = serializers.SerializerMethodField()
    release_unix_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = db.Quiz
        fields = [
            "title",
            "slug",
            "start_unix_timestamp",
            "end_unix_timestamp",
            "release_unix_timestamp",
        ]

    def get_release_unix_timestamp(self, quiz: db.Quiz) -> int:
        return int(quiz.release_answers_at.timestamp())

    def get_start_unix_timestamp(self, quiz: db.Quiz) -> int:
        return int(quiz.starts_at.timestamp())

    def get_end_unix_timestamp(self, quiz: db.Quiz) -> int:
        return int(quiz.ends_at.timestamp())


class AllQuizzesListSerializer(CourseQuizzesListSerializer):
    course_slug = serializers.CharField(source="offering.course.slug", read_only=True)

    class Meta(CourseQuizzesListSerializer.Meta):
        fields = CourseQuizzesListSerializer.Meta.fields + ["course_slug"]
