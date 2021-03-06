import datetime
from szurubooru import search
from szurubooru.api.base_api import BaseApi
from szurubooru.func import auth, tags, posts, snapshots, favorites, scores

class PostListApi(BaseApi):
    def __init__(self):
        super().__init__()
        self._search_executor = search.SearchExecutor(search.PostSearchConfig())

    def get(self, ctx):
        auth.verify_privilege(ctx.user, 'posts:list')
        self._search_executor.config.user = ctx.user
        return self._search_executor.execute_and_serialize(
            ctx, lambda post: posts.serialize_post(post, ctx.user))

    def post(self, ctx):
        auth.verify_privilege(ctx.user, 'posts:create')
        content = ctx.get_file('content', required=True)
        tag_names = ctx.get_param_as_list('tags', required=True)
        safety = ctx.get_param_as_string('safety', required=True)
        source = ctx.get_param_as_string('source', required=False, default=None)
        if ctx.has_param('contentUrl') and not source:
            source = ctx.get_param_as_string('contentUrl')
        relations = ctx.get_param_as_list('relations', required=False) or []
        notes = ctx.get_param_as_list('notes', required=False) or []
        flags = ctx.get_param_as_list('flags', required=False) or []

        post = posts.create_post(content, tag_names, ctx.user)
        posts.update_post_safety(post, safety)
        posts.update_post_source(post, source)
        posts.update_post_relations(post, relations)
        posts.update_post_notes(post, notes)
        posts.update_post_flags(post, flags)
        if ctx.has_file('thumbnail'):
            posts.update_post_thumbnail(post, ctx.get_file('thumbnail'))
        ctx.session.add(post)
        snapshots.save_entity_creation(post, ctx.user)
        ctx.session.commit()
        tags.export_to_json()
        return posts.serialize_post_with_details(post, ctx.user)

class PostDetailApi(BaseApi):
    def get(self, ctx, post_id):
        auth.verify_privilege(ctx.user, 'posts:view')
        post = posts.get_post_by_id(post_id)
        return posts.serialize_post_with_details(post, ctx.user)

    def put(self, ctx, post_id):
        post = posts.get_post_by_id(post_id)
        if ctx.has_file('content'):
            auth.verify_privilege(ctx.user, 'posts:edit:content')
            posts.update_post_content(post, ctx.get_file('content'))
        if ctx.has_param('tags'):
            auth.verify_privilege(ctx.user, 'posts:edit:tags')
            posts.update_post_tags(post, ctx.get_param_as_list('tags'))
        if ctx.has_param('safety'):
            auth.verify_privilege(ctx.user, 'posts:edit:safety')
            posts.update_post_safety(post, ctx.get_param_as_string('safety'))
        if ctx.has_param('source'):
            auth.verify_privilege(ctx.user, 'posts:edit:source')
            posts.update_post_source(post, ctx.get_param_as_string('source'))
        elif ctx.has_param('contentUrl'):
            posts.update_post_source(post, ctx.get_param_as_string('contentUrl'))
        if ctx.has_param('relations'):
            auth.verify_privilege(ctx.user, 'posts:edit:relations')
            posts.update_post_relations(post, ctx.get_param_as_list('relations'))
        if ctx.has_param('notes'):
            auth.verify_privilege(ctx.user, 'posts:edit:notes')
            posts.update_post_notes(post, ctx.get_param_as_list('notes'))
        if ctx.has_param('flags'):
            auth.verify_privilege(ctx.user, 'posts:edit:flags')
            posts.update_post_flags(post, ctx.get_param_as_list('flags'))
        if ctx.has_file('thumbnail'):
            auth.verify_privilege(ctx.user, 'posts:edit:thumbnail')
            posts.update_post_thumbnail(post, ctx.get_file('thumbnail'))
        post.last_edit_time = datetime.datetime.now()
        ctx.session.flush()
        snapshots.save_entity_modification(post, ctx.user)
        ctx.session.commit()
        tags.export_to_json()
        return posts.serialize_post_with_details(post, ctx.user)

    def delete(self, ctx, post_id):
        auth.verify_privilege(ctx.user, 'posts:delete')
        post = posts.get_post_by_id(post_id)
        snapshots.save_entity_deletion(post, ctx.user)
        ctx.session.delete(post)
        ctx.session.commit()
        tags.export_to_json()
        return {}

class PostFeatureApi(BaseApi):
    def post(self, ctx):
        auth.verify_privilege(ctx.user, 'posts:feature')
        post_id = ctx.get_param_as_int('id', required=True)
        post = posts.get_post_by_id(post_id)
        featured_post = posts.try_get_featured_post()
        if featured_post and featured_post.post_id == post.post_id:
            raise posts.PostAlreadyFeaturedError(
                'Post %r is already featured.' % post_id)
        posts.feature_post(post, ctx.user)
        if featured_post:
            snapshots.save_entity_modification(featured_post, ctx.user)
        snapshots.save_entity_modification(post, ctx.user)
        ctx.session.commit()
        return posts.serialize_post_with_details(post, ctx.user)

    def get(self, ctx):
        post = posts.try_get_featured_post()
        return posts.serialize_post_with_details(post, ctx.user)

class PostScoreApi(BaseApi):
    def put(self, ctx, post_id):
        auth.verify_privilege(ctx.user, 'posts:score')
        post = posts.get_post_by_id(post_id)
        score = ctx.get_param_as_int('score', required=True)
        scores.set_score(post, ctx.user, score)
        ctx.session.commit()
        return posts.serialize_post_with_details(post, ctx.user)

    def delete(self, ctx, post_id):
        auth.verify_privilege(ctx.user, 'posts:score')
        post = posts.get_post_by_id(post_id)
        scores.delete_score(post, ctx.user)
        ctx.session.commit()
        return posts.serialize_post_with_details(post, ctx.user)

class PostFavoriteApi(BaseApi):
    def post(self, ctx, post_id):
        auth.verify_privilege(ctx.user, 'posts:favorite')
        post = posts.get_post_by_id(post_id)
        favorites.set_favorite(post, ctx.user)
        ctx.session.commit()
        return posts.serialize_post_with_details(post, ctx.user)

    def delete(self, ctx, post_id):
        auth.verify_privilege(ctx.user, 'posts:favorite')
        post = posts.get_post_by_id(post_id)
        favorites.unset_favorite(post, ctx.user)
        ctx.session.commit()
        return posts.serialize_post_with_details(post, ctx.user)
