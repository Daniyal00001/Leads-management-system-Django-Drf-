from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import User
from .models import Comment, CommentAttachment


class CommentAttachmentSerializer(serializers.ModelSerializer):  #BASE
    class Meta:
        model = CommentAttachment
        fields = ["id", "image"]


class UserBasicSerializer(serializers.ModelSerializer):  #base
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]

# ==========================================================================

 #    Used for reading comments (GET) — includes nested attachments and user info.
class CommentSerializer(serializers.ModelSerializer):    
    user = UserBasicSerializer(read_only=True)
    attachments = CommentAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user", "body", "attachments", "created_at"]



 # Used for writing (POST) — takes model name + object id directly from
   # the client instead of exposing raw content_type/object_id, since the
   #frontend shouldn't need to know Django's internal ContentType IDs.
class CommentCreateSerializer(serializers.Serializer): # not a model serializer
    model_name = serializers.ChoiceField(choices=["lead", "phase", "project"])
    object_id = serializers.IntegerField()
    body = serializers.CharField(allow_blank=False)
    images = serializers.ListField(
        child=serializers.ImageField(),  #images wali list ke andar har item image type ka hona chahiye
        required=False,
        default=list,
    )

    MODEL_MAP = {
        "lead": ("leads", "lead"),
        "phase": ("leads", "phase"),
        "project": ("projects", "project"),
    }

    def validate(self, attrs):
        app_label, model = self.MODEL_MAP[attrs["model_name"]]
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Invalid target model.")

        target_model = content_type.model_class()
        if not target_model.objects.filter(pk=attrs["object_id"]).exists():
            raise serializers.ValidationError(f"{attrs['model_name']} with this id does not exist.")

        attrs["content_type"] = content_type
        return attrs