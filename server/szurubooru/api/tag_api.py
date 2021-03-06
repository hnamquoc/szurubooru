import datetime
from szurubooru import search
from szurubooru.api.base_api import BaseApi
from szurubooru.func import auth, tags, snapshots

class TagListApi(BaseApi):
    def __init__(self):
        super().__init__()
        self._search_executor = search.SearchExecutor(search.TagSearchConfig())

    def get(self, ctx):
        auth.verify_privilege(ctx.user, 'tags:list')
        return self._search_executor.execute_and_serialize(
            ctx, tags.serialize_tag)

    def post(self, ctx):
        auth.verify_privilege(ctx.user, 'tags:create')

        names = ctx.get_param_as_list('names', required=True)
        category = ctx.get_param_as_string('category', required=True)
        suggestions = ctx.get_param_as_list(
            'suggestions', required=False, default=[])
        implications = ctx.get_param_as_list(
            'implications', required=False, default=[])

        tag = tags.create_tag(names, category, suggestions, implications)
        ctx.session.add(tag)
        ctx.session.flush()
        snapshots.save_entity_creation(tag, ctx.user)
        ctx.session.commit()
        tags.export_to_json()
        return tags.serialize_tag_with_details(tag)

class TagDetailApi(BaseApi):
    def get(self, ctx, tag_name):
        auth.verify_privilege(ctx.user, 'tags:view')
        tag = tags.get_tag_by_name(tag_name)
        return tags.serialize_tag_with_details(tag)

    def put(self, ctx, tag_name):
        tag = tags.get_tag_by_name(tag_name)
        if ctx.has_param('names'):
            auth.verify_privilege(ctx.user, 'tags:edit:names')
            tags.update_tag_names(tag, ctx.get_param_as_list('names'))
        if ctx.has_param('category'):
            auth.verify_privilege(ctx.user, 'tags:edit:category')
            tags.update_tag_category_name(
                tag, ctx.get_param_as_string('category'))
        if ctx.has_param('suggestions'):
            auth.verify_privilege(ctx.user, 'tags:edit:suggestions')
            tags.update_tag_suggestions(
                tag, ctx.get_param_as_list('suggestions'))
        if ctx.has_param('implications'):
            auth.verify_privilege(ctx.user, 'tags:edit:implications')
            tags.update_tag_implications(
                tag, ctx.get_param_as_list('implications'))
        tag.last_edit_time = datetime.datetime.now()
        ctx.session.flush()
        snapshots.save_entity_modification(tag, ctx.user)
        ctx.session.commit()
        tags.export_to_json()
        return tags.serialize_tag_with_details(tag)

    def delete(self, ctx, tag_name):
        tag = tags.get_tag_by_name(tag_name)
        if tag.post_count > 0:
            raise tags.TagIsInUseError(
                'Tag has some usages and cannot be deleted. ' +
                'Please untag relevant posts first.')
        auth.verify_privilege(ctx.user, 'tags:delete')
        snapshots.save_entity_deletion(tag, ctx.user)
        tags.delete(tag)
        ctx.session.commit()
        tags.export_to_json()
        return {}

class TagMergeApi(BaseApi):
    def post(self, ctx):
        source_tag_name = ctx.get_param_as_string('remove', required=True) or ''
        target_tag_name = ctx.get_param_as_string('mergeTo', required=True) or ''
        source_tag = tags.get_tag_by_name(source_tag_name)
        target_tag = tags.get_tag_by_name(target_tag_name)
        if source_tag.tag_id == target_tag.tag_id:
            raise tags.InvalidTagRelationError('Cannot merge tag with itself.')
        auth.verify_privilege(ctx.user, 'tags:merge')
        snapshots.save_entity_deletion(source_tag, ctx.user)
        tags.merge_tags(source_tag, target_tag)
        ctx.session.commit()
        tags.export_to_json()
        return tags.serialize_tag_with_details(target_tag)

class TagSiblingsApi(BaseApi):
    def get(self, ctx, tag_name):
        auth.verify_privilege(ctx.user, 'tags:view')
        tag = tags.get_tag_by_name(tag_name)
        result = tags.get_tag_siblings(tag)
        serialized_siblings = []
        for sibling, occurrences in result:
            serialized_siblings.append({
                'tag': tags.serialize_tag(sibling),
                'occurrences': occurrences
            })
        return {'siblings': serialized_siblings}
