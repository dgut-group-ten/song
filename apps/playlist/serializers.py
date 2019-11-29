from django.db.models import Count
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from song.models import PlayList, Tag
from song.serializers import SongListSerializer


class TagSerializer(serializers.ModelSerializer):
    times = serializers.SerializerMethodField(read_only=True)

    def get_times(self, obj):
        queryset = Tag.objects.filter(name=obj.name)
        tags = queryset.annotate(times=Count('playlist_tag'))

        return tags[0].times

    class Meta:
        model = Tag
        fields = "__all__"


class PlayListSerializer(serializers.ModelSerializer):
    """关于歌单的序列化函数"""

    lid = serializers.IntegerField(label='ID', validators=[UniqueValidator(queryset=PlayList.objects.all())],
                                   help_text='空的话， 就是自增序列', required=False)
    tags = serializers.SerializerMethodField()
    stags = serializers.CharField(label="文章标签的字符串", help_text='中间用空格隔开', allow_null=True, allow_blank=True,
                                  write_only=True)
    tracks = serializers.SerializerMethodField(label="歌曲目录")

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def get_tracks(self, obj):
        if self.context['view'].action == 'retrieve':
            return SongListSerializer(obj.tracks, many=True, context={'request': self.context['request']}).data
        return [song.sid for song in obj.tracks.all()]

    class Meta:
        model = PlayList
        fields = "__all__"
        read_only_fields = ('creator', 'tags')

    def create(self, validated_data):
        tags = validated_data.pop('stags')
        playlist = super().create(validated_data)
        playlist.tags.set(get_tag_list(tags))

        return playlist

    def update(self, instance, validated_data):
        tags = validated_data.pop('stags')
        playlist = super().update(instance, validated_data)
        playlist.tags.set(get_tag_list(tags))

        return playlist


def get_tag_list(tags):
    tag_list = []

    try:
        for tag in tags.split(' '):
            if tag:
                tag, created = Tag.objects.update_or_create(name=tag)
                tag_list.append(tag)
    except Exception as e:
        tag_list = []
        print(e)
    return tag_list