import datetime
import pytest
from szurubooru import db, errors, search

@pytest.fixture
def fav_factory(user_factory):
    def factory(post, user=None):
        return db.PostFavorite(
            post=post, user=user or user_factory(), time=datetime.datetime.now())
    return factory

@pytest.fixture
def score_factory(user_factory):
    def factory(post, user=None, score=1):
        return db.PostScore(
            post=post,
            user=user or user_factory(),
            time=datetime.datetime.now(),
            score=score)
    return factory

@pytest.fixture
def note_factory():
    def factory(post=None):
        if post:
            return db.PostNote(polygon='...', text='...', post=post)
        return db.PostNote(polygon='...', text='...')
    return factory

@pytest.fixture
def feature_factory(user_factory):
    def factory(post=None):
        if post:
            return db.PostFeature(
                time=datetime.datetime.now(), user=user_factory(), post=post)
        return db.PostFeature(time=datetime.datetime.now(), user=user_factory())
    return factory

@pytest.fixture
def executor(user_factory):
    return search.SearchExecutor(search.PostSearchConfig())

@pytest.fixture
def auth_executor(executor, user_factory):
    def wrapper():
        auth_user = user_factory()
        db.session.add(auth_user)
        db.session.flush()
        executor.config.user = auth_user
        return auth_user
    return wrapper

@pytest.fixture
def verify_unpaged(executor):
    def verify(input, expected_post_ids, test_order=False):
        actual_count, actual_posts = executor.execute(
            input, page=1, page_size=100)
        actual_post_ids = list([p.post_id for p in actual_posts])
        assert actual_count == len(expected_post_ids)
        if not test_order:
            actual_post_ids = sorted(actual_post_ids)
            expected_post_ids = sorted(expected_post_ids)
        assert actual_post_ids == expected_post_ids
    return verify

@pytest.mark.parametrize('input,expected_post_ids', [
    ('id:1', [1]),
    ('id:3', [3]),
    ('id:1,3', [1, 3]),
])
def test_filter_by_id(verify_unpaged, post_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('tag:t1', [1]),
    ('tag:t2', [2]),
    ('tag:t1,t2', [1, 2]),
    ('tag:t4a', [4]),
    ('tag:t4b', [4]),
])
def test_filter_by_tag(
        verify_unpaged, post_factory, tag_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post4 = post_factory(id=4)
    post1.tags=[tag_factory(names=['t1'])]
    post2.tags=[tag_factory(names=['t2'])]
    post3.tags=[tag_factory(names=['t3'])]
    post4.tags=[tag_factory(names=['t4a', 't4b'])]
    db.session.add_all([post1, post2, post3, post4])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('score:1', [1]),
    ('score:3', [3]),
    ('score:1,3', [1, 3]),
])
def test_filter_by_score(
        verify_unpaged, post_factory, user_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    for post in [post1, post2, post3]:
        db.session.add(
            db.PostScore(
                score=post.post_id,
                time=datetime.datetime.now(),
                post=post,
                user=user_factory()))
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('uploader:u1', [1]),
    ('uploader:u3', [3]),
    ('uploader:u1,u3', [1, 3]),
    ('upload:u1', [1]),
    ('upload:u3', [3]),
    ('upload:u1,u3', [1, 3]),
    ('submit:u1', [1]),
    ('submit:u3', [3]),
    ('submit:u1,u3', [1, 3]),
])
def test_filter_by_uploader(
        verify_unpaged, post_factory, user_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post1.user = user_factory(name='u1')
    post2.user = user_factory(name='u2')
    post3.user = user_factory(name='u3')
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('comment:u1', [1]),
    ('comment:u3', [3]),
    ('comment:u1,u3', [1, 3]),
])
def test_filter_by_commenter(
        verify_unpaged,
        post_factory,
        user_factory,
        comment_factory,
        input,
        expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    db.session.add_all([
        comment_factory(post=post1, user=user_factory(name='u1')),
        comment_factory(post=post2, user=user_factory(name='u2')),
        comment_factory(post=post3, user=user_factory(name='u3')),
        post1, post2, post3,
    ])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('fav:u1', [1]),
    ('fav:u3', [3]),
    ('fav:u1,u3', [1, 3]),
])
def test_filter_by_favorite(
        verify_unpaged,
        post_factory,
        user_factory,
        fav_factory,
        input,
        expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    db.session.add_all([
        fav_factory(post=post1, user=user_factory(name='u1')),
        fav_factory(post=post2, user=user_factory(name='u2')),
        fav_factory(post=post3, user=user_factory(name='u3')),
        post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('tag-count:1', [1]),
    ('tag-count:3', [3]),
    ('tag-count:1,3', [1, 3]),
])
def test_filter_by_tag_count(
        verify_unpaged, post_factory, tag_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post1.tags=[tag_factory()]
    post2.tags=[tag_factory(), tag_factory()]
    post3.tags=[tag_factory(), tag_factory(), tag_factory()]
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('comment-count:1', [1]),
    ('comment-count:3', [3]),
    ('comment-count:1,3', [1, 3]),
])
def test_filter_by_comment_count(
        verify_unpaged, post_factory, comment_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    db.session.add_all([
        comment_factory(post=post1),
        comment_factory(post=post2),
        comment_factory(post=post2),
        comment_factory(post=post3),
        comment_factory(post=post3),
        comment_factory(post=post3),
        post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('fav-count:1', [1]),
    ('fav-count:3', [3]),
    ('fav-count:1,3', [1, 3]),
])
def test_filter_by_favorite_count(
        verify_unpaged, post_factory, fav_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    db.session.add_all([
        fav_factory(post=post1),
        fav_factory(post=post2),
        fav_factory(post=post2),
        fav_factory(post=post3),
        fav_factory(post=post3),
        fav_factory(post=post3),
        post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('note-count:1', [1]),
    ('note-count:3', [3]),
    ('note-count:1,3', [1, 3]),
])
def test_filter_by_note_count(
        verify_unpaged, post_factory, note_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post1.notes=[note_factory()]
    post2.notes=[note_factory(), note_factory()]
    post3.notes=[note_factory(), note_factory(), note_factory()]
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('feature-count:1', [1]),
    ('feature-count:3', [3]),
    ('feature-count:1,3', [1, 3]),
])
def test_filter_by_feature_count(
        verify_unpaged, post_factory, feature_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post1.features=[feature_factory()]
    post2.features=[feature_factory(), feature_factory()]
    post3.features=[feature_factory(), feature_factory(), feature_factory()]
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('type:image', [1]),
    ('type:anim', [2]),
    ('type:animation', [2]),
    ('type:gif', [2]),
    ('type:video', [3]),
    ('type:webm', [3]),
    ('type:flash', [4]),
    ('type:swf', [4]),
])
def test_filter_by_type(verify_unpaged, post_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post4 = post_factory(id=4)
    post1.type = db.Post.TYPE_IMAGE
    post2.type = db.Post.TYPE_ANIMATION
    post3.type = db.Post.TYPE_VIDEO
    post4.type = db.Post.TYPE_FLASH
    db.session.add_all([post1, post2, post3, post4])
    verify_unpaged(input, expected_post_ids)

def test_filter_by_invalid_type(executor):
    with pytest.raises(errors.SearchError):
        actual_count, actual_posts = executor.execute(
            'type:invalid', page=1, page_size=100)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('file-size:100', [1]),
    ('file-size:102', [3]),
    ('file-size:100,102', [1, 3]),
])
def test_filter_by_file_size(
        verify_unpaged, post_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post1.file_size = 100
    post2.file_size = 101
    post3.file_size = 102
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('image-width:100', [1]),
    ('image-width:102', [3]),
    ('image-width:100,102', [1, 3]),
    ('image-height:200', [1]),
    ('image-height:202', [3]),
    ('image-height:200,202', [1, 3]),
    ('image-area:20000', [1]),
    ('image-area:20604', [3]),
    ('image-area:20000,20604', [1, 3]),
])
def test_filter_by_image_size(
        verify_unpaged, post_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post1.canvas_width = 100
    post2.canvas_width = 101
    post3.canvas_width = 102
    post1.canvas_height = 200
    post2.canvas_height = 201
    post3.canvas_height = 202
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('creation-date:2014', [1]),
    ('creation-date:2016', [3]),
    ('creation-date:2014,2016', [1, 3]),
    ('creation-time:2014', [1]),
    ('creation-time:2016', [3]),
    ('creation-time:2014,2016', [1, 3]),
    ('date:2014', [1]),
    ('date:2016', [3]),
    ('date:2014,2016', [1, 3]),
    ('time:2014', [1]),
    ('time:2016', [3]),
    ('time:2014,2016', [1, 3]),
])
def test_filter_by_creation_time(
        verify_unpaged, post_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post1.creation_time = datetime.datetime(2014, 1, 1)
    post2.creation_time = datetime.datetime(2015, 1, 1)
    post3.creation_time = datetime.datetime(2016, 1, 1)
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('last-edit-date:2014', [1]),
    ('last-edit-date:2016', [3]),
    ('last-edit-date:2014,2016', [1, 3]),
    ('last-edit-time:2014', [1]),
    ('last-edit-time:2016', [3]),
    ('last-edit-time:2014,2016', [1, 3]),
    ('edit-date:2014', [1]),
    ('edit-date:2016', [3]),
    ('edit-date:2014,2016', [1, 3]),
    ('edit-time:2014', [1]),
    ('edit-time:2016', [3]),
    ('edit-time:2014,2016', [1, 3]),
])
def test_filter_by_last_edit_time(
        verify_unpaged, post_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post1.last_edit_time = datetime.datetime(2014, 1, 1)
    post2.last_edit_time = datetime.datetime(2015, 1, 1)
    post3.last_edit_time = datetime.datetime(2016, 1, 1)
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('comment-date:2014', [1]),
    ('comment-date:2016', [3]),
    ('comment-date:2014,2016', [1, 3]),
    ('comment-time:2014', [1]),
    ('comment-time:2016', [3]),
    ('comment-time:2014,2016', [1, 3]),
])
def test_filter_by_comment_date(
        verify_unpaged, post_factory, comment_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    comment1 = comment_factory(post=post1)
    comment2 = comment_factory(post=post2)
    comment3 = comment_factory(post=post3)
    comment1.last_edit_time = datetime.datetime(2014, 1, 1)
    comment2.last_edit_time = datetime.datetime(2015, 1, 1)
    comment3.last_edit_time = datetime.datetime(2016, 1, 1)
    db.session.add_all([post1, post2, post3, comment1, comment2, comment3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('fav-date:2014', [1]),
    ('fav-date:2016', [3]),
    ('fav-date:2014,2016', [1, 3]),
    ('fav-time:2014', [1]),
    ('fav-time:2016', [3]),
    ('fav-time:2014,2016', [1, 3]),
])
def test_filter_by_fav_date(
        verify_unpaged, post_factory, fav_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    fav1 = fav_factory(post=post1)
    fav2 = fav_factory(post=post2)
    fav3 = fav_factory(post=post3)
    fav1.time = datetime.datetime(2014, 1, 1)
    fav2.time = datetime.datetime(2015, 1, 1)
    fav3.time = datetime.datetime(2016, 1, 1)
    db.session.add_all([post1, post2, post3, fav1, fav2, fav3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input,expected_post_ids', [
    ('feature-date:2014', [1]),
    ('feature-date:2016', [3]),
    ('feature-date:2014,2016', [1, 3]),
    ('feature-time:2014', [1]),
    ('feature-time:2016', [3]),
    ('feature-time:2014,2016', [1, 3]),
])
def test_filter_by_feature_date(
        verify_unpaged, post_factory, feature_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    feature1 = feature_factory(post=post1)
    feature2 = feature_factory(post=post2)
    feature3 = feature_factory(post=post3)
    feature1.time = datetime.datetime(2014, 1, 1)
    feature2.time = datetime.datetime(2015, 1, 1)
    feature3.time = datetime.datetime(2016, 1, 1)
    db.session.add_all([post1, post2, post3, feature1, feature2, feature3])
    verify_unpaged(input, expected_post_ids)

@pytest.mark.parametrize('input', [
    'sort:random',
    'sort:id',
    'sort:score',
    'sort:tag-count',
    'sort:comment-count',
    'sort:fav-count',
    'sort:note-count',
    'sort:feature-count',
    'sort:file-size',
    'sort:image-width',
    'sort:width',
    'sort:image-height',
    'sort:height',
    'sort:image-area',
    'sort:area',
    'sort:creation-date',
    'sort:creation-time',
    'sort:date',
    'sort:time',
    'sort:last-edit-date',
    'sort:last-edit-time',
    'sort:edit-date',
    'sort:edit-time',
    'sort:comment-date',
    'sort:comment-time',
    'sort:fav-date',
    'sort:fav-time',
    'sort:feature-date',
    'sort:feature-time',
])
def test_sort_tokens(verify_unpaged, post_factory, input):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    db.session.add_all([post1, post2, post3])
    verify_unpaged(input, [1, 2, 3])

@pytest.mark.parametrize('input,expected_post_ids', [
    ('', [1, 2, 3, 4]),
    ('t1', [1]),
    ('t2', [2]),
    ('t1,t2', [1, 2]),
    ('t4a', [4]),
    ('t4b', [4]),
])
def test_anonymous(
        verify_unpaged, post_factory, tag_factory, input, expected_post_ids):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post4 = post_factory(id=4)
    post1.tags=[tag_factory(names=['t1'])]
    post2.tags=[tag_factory(names=['t2'])]
    post3.tags=[tag_factory(names=['t3'])]
    post4.tags=[tag_factory(names=['t4a', 't4b'])]
    db.session.add_all([post1, post2, post3, post4])
    verify_unpaged(input, expected_post_ids)

def test_own_liked(
        auth_executor, post_factory, score_factory, user_factory, verify_unpaged):
    auth_user = auth_executor()
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    db.session.add_all([
        score_factory(post=post1, user=auth_user, score=1),
        score_factory(post=post2, user=user_factory(name='unrelated'), score=1),
        score_factory(post=post3, user=auth_user, score=-1),
        post1, post2, post3,
    ])
    verify_unpaged('special:liked', [1])
    verify_unpaged('-special:liked', [2, 3])

def test_own_disliked(
        auth_executor, post_factory, score_factory, user_factory, verify_unpaged):
    auth_user = auth_executor()
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    db.session.add_all([
        score_factory(post=post1, user=auth_user, score=-1),
        score_factory(post=post2, user=user_factory(name='unrelated'), score=-1),
        score_factory(post=post3, user=auth_user, score=1),
        post1, post2, post3,
    ])
    verify_unpaged('special:disliked', [1])
    verify_unpaged('-special:disliked', [2, 3])

def test_own_fav(
        auth_executor, post_factory, fav_factory, user_factory, verify_unpaged):
    auth_user = auth_executor()
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    db.session.add_all([
        fav_factory(post=post1, user=auth_user),
        fav_factory(post=post2, user=user_factory(name='unrelated')),
        post1, post2,
    ])
    verify_unpaged('special:fav', [1])
    verify_unpaged('-special:fav', [2])

def test_tumbleweed(
        executor,
        post_factory,
        fav_factory,
        comment_factory,
        score_factory,
        verify_unpaged):
    post1 = post_factory(id=1)
    post2 = post_factory(id=2)
    post3 = post_factory(id=3)
    post4 = post_factory(id=4)
    db.session.add_all([
        comment_factory(post=post1),
        score_factory(post=post2),
        fav_factory(post=post3),
        post1, post2, post3, post4,
    ])
    verify_unpaged('special:tumbleweed', [4])
    verify_unpaged('-special:tumbleweed', [1, 2, 3])
