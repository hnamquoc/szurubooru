import os
import pytest
from szurubooru import api, config, db, errors
from szurubooru.func import util, tag_categories

@pytest.fixture
def test_ctx(
        tmpdir,
        config_injector,
        context_factory,
        user_factory,
        tag_category_factory):
    config_injector({
        'data_dir': str(tmpdir),
        'tag_category_name_regex': '^[^!]*$',
        'privileges': {
            'tag_categories:edit:name': db.User.RANK_REGULAR,
            'tag_categories:edit:color': db.User.RANK_REGULAR,
        },
    })
    ret = util.dotdict()
    ret.context_factory = context_factory
    ret.user_factory = user_factory
    ret.tag_category_factory = tag_category_factory
    ret.api = api.TagCategoryDetailApi()
    return ret

def test_simple_updating(test_ctx):
    category = test_ctx.tag_category_factory(name='name', color='black')
    db.session.add(category)
    db.session.commit()
    result = test_ctx.api.put(
        test_ctx.context_factory(
            input={
                'name': 'changed',
                'color': 'white',
            },
            user=test_ctx.user_factory(rank=db.User.RANK_REGULAR)),
        'name')
    assert result['tagCategory'] == {
        'name': 'changed',
        'color': 'white',
        'usages': 0,
    }
    assert len(result['snapshots']) == 1
    assert tag_categories.try_get_category_by_name('name') is None
    category = tag_categories.get_category_by_name('changed')
    assert category is not None
    assert category.name == 'changed'
    assert category.color == 'white'
    assert os.path.exists(os.path.join(config.config['data_dir'], 'tags.json'))

@pytest.mark.parametrize('input', [
    {'name': None},
    {'name': ''},
    {'name': '!bad'},
    {'color': None},
    {'color': ''},
    {'color': '; float:left'},
])
def test_trying_to_pass_invalid_input(test_ctx, input):
    db.session.add(test_ctx.tag_category_factory(name='meta', color='black'))
    db.session.commit()
    with pytest.raises(tag_categories.InvalidTagCategoryNameError):
        test_ctx.api.put(
            test_ctx.context_factory(
                input=input,
                user=test_ctx.user_factory(rank=db.User.RANK_REGULAR)),
            'meta')

@pytest.mark.parametrize('field', ['name', 'color'])
def test_omitting_optional_field(test_ctx, field):
    db.session.add(test_ctx.tag_category_factory(name='name', color='black'))
    db.session.commit()
    input = {
        'name': 'changed',
        'color': 'white',
    }
    del input[field]
    result = test_ctx.api.put(
        test_ctx.context_factory(
            input=input,
            user=test_ctx.user_factory(rank=db.User.RANK_REGULAR)),
        'name')
    assert result is not None

def test_trying_to_update_non_existing(test_ctx):
    with pytest.raises(tag_categories.TagCategoryNotFoundError):
        test_ctx.api.put(
            test_ctx.context_factory(
                input={'name': ['dummy']},
                user=test_ctx.user_factory(rank=db.User.RANK_REGULAR)),
            'bad')

@pytest.mark.parametrize('new_name', ['cat', 'CAT'])
def test_reusing_own_name(test_ctx, new_name):
    db.session.add(test_ctx.tag_category_factory(name='cat', color='black'))
    db.session.commit()
    result = test_ctx.api.put(
        test_ctx.context_factory(
            input={'name': new_name},
            user=test_ctx.user_factory(rank=db.User.RANK_REGULAR)),
        'cat')
    assert result['tagCategory']['name'] == new_name
    category = tag_categories.get_category_by_name('cat')
    assert category.name == new_name

@pytest.mark.parametrize('dup_name', ['cat1', 'CAT1'])
def test_trying_to_use_existing_name(test_ctx, dup_name):
    db.session.add_all([
        test_ctx.tag_category_factory(name='cat1', color='black'),
        test_ctx.tag_category_factory(name='cat2', color='black')])
    db.session.commit()
    with pytest.raises(tag_categories.TagCategoryAlreadyExistsError):
        test_ctx.api.put(
            test_ctx.context_factory(
                input={'name': dup_name},
                user=test_ctx.user_factory(rank=db.User.RANK_REGULAR)),
            'cat2')

@pytest.mark.parametrize('input', [
    {'name': 'whatever'},
    {'color': 'whatever'},
])
def test_trying_to_update_without_privileges(test_ctx, input):
    db.session.add(test_ctx.tag_category_factory(name='dummy'))
    db.session.commit()
    with pytest.raises(errors.AuthError):
        test_ctx.api.put(
            test_ctx.context_factory(
                input=input,
                user=test_ctx.user_factory(rank=db.User.RANK_ANONYMOUS)),
            'dummy')
