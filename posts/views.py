from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from .models import Post, Comment
import requests
import json



def index(request):
    # API_KEY = json.loads(open('secrets.json').read())
    api_key = 'caea966f6e10b1fbcfc446cd0052d5cd' 

    # 최신 상영작을 평점 순으로 나열하여 5개만 불러옵니다.
    now_playing_url = 'https://api.themoviedb.org/3/movie/now_playing?api_key={}&language=ko-KR&page=1&region=KR'.format(api_key)
    now_playing_response = requests.get(now_playing_url).json()
    now_playing = sorted(now_playing_response['results'], key=lambda x:x['vote_average'], reverse=True)[:5]

    # 명작 영화를 평점 순으로 나열하여 5개만 불러옵니다.
    top_rated_url = 'https://api.themoviedb.org/3/movie/top_rated?api_key={}&language=ko-KR&page=1'.format(api_key)
    top_rated_response = requests.get(top_rated_url).json()
    top_rated = sorted(top_rated_response['results'], key=lambda x:x['vote_average'], reverse=True)[:5]

    # 장르 번호를 딕셔너리로 만들어두었으니 활용하시면 됩니다. ^^
    genre_dict = {
        28: '액션',
        12: '모험',
        16: '애니메이션',
        35: '코미디',
        80: '범죄',
        99: '다큐멘터리',
        18: '드라마',
        10751: '가족',
        14: '판타지',
        36: '역사',
        27: '공포',
        10402: '음악',
        9648: '미스터리',
        10749: '로맨스',
        878: 'SF',
        10770: 'TV 영화',
        53: '스릴러',
        10752: '전쟁',
        37: '서부'
    }
    
    # 장르별 영화를 불러옵니다.
    # 템플릿에서 genre_ids에 원하는 장르 번호가 있는지 확인하여 장르별 영화를 불러올 수 있습니다.
    # 단, 평균적으로 5개 이상의 장르별 영화를 불러오려면 여러 개 페이지를 참여해야 하므로 for문을 사용했습니다.
    # 템플릿에서는 페이지별 영화정보를 불러오는 for문, 한 페이지의 영화정보들에서 하나씩 영화 정보를 불러오는 for문, 이렇게 2중 for문을 사용해야 합니다... ㅠㅠ   
    genre_movie_list = list()
    for page in range(1, 5):
        genre_url = 'https://api.themoviedb.org/3/movie/top_rated?api_key={}&language=ko-KR&page={}'.format(api_key, page)
        genre_response = requests.get(genre_url).json()
        genre = sorted(genre_response['results'], key=lambda x:x['vote_average'], reverse=True)
        genre_movie_list.append(genre)

    context = {
        'now_playing': now_playing,
        'top_rated': top_rated,
        'genre_movie_list': genre_movie_list,
    }
    return render(request, 'posts/index.html', context)


# tmdb API를 이용하여 검색한 결과를 가져와 상세정보 출력
def search(request):
    TMDB_API_KEY = 'caea966f6e10b1fbcfc446cd0052d5cd'

    movie_title = request.GET.get('title')

    url ='https://api.themoviedb.org/3/search/movie'

    params = {
        'api_key': TMDB_API_KEY,
        'query': movie_title,
        'language': 'ko-kr',
    }

    response = requests.get(url, params=params)
    search_data = response.json()

    image_url = 'https://image.tmdb.org/t/p/w200' # w로 사이즈 조절
    for movie in search_data['results']:
        if movie['poster_path']:
            movie['poster_path'] = image_url + movie['poster_path']
        else:
            movie['poster_path'] = '이미지 없음'


    context = {
        'search_data': search_data
    }

    return render(request, 'posts/search.html', context)


def movie_detail(request):
    pass


def post_detail(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('posts:post_detail', post.pk)
    else:
        form = PostForm()
    context = {
        'form': form,
    }
    return render(request, 'posts/create.html', context)


@login_required
def update(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    if request.user == post.user:
        if request.method == 'POST':
            form = PostForm(request.POST, instance=post)
            if form.is_valid():
                form.save()
                return redirect('posts:post_detail', post.pk)
        else:
            form = PostForm(instance=post)
    else:
        return redirect('posts:post_detail', post.pk)
    context = {
        'form': form,
    }
    return render(request, 'posts/update.html', context)


def delete(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    if request.user == post.user:
        post.delete()
        return redirect('posts:movie_detail')


@login_required
def post_likes(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    if request.user in post.like_users.all():
        post.like_users.remove(request.user)
    else:
        post.like_users.add(request.user)
    return redirect('posts:post_detail', post.pk)


@login_required
def comment_create(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect('posts:post_detail', post.pk)


@login_required
def comment_delete(request, post_pk, comment_pk):
    comment = Comment.objects.get(pk=comment_pk)
    if request.user == comment.user:
        comment.delete()
    return redirect('posts:post_detail', post_pk)


@login_required
def comment_likes(request, post_pk, comment_pk):
    comment = Post.objects.get(pk=comment_pk)
    if request.user in comment.like_users.all():
        comment.like_users.remove(request.user)
    else:
        comment.like_users.add(request.user)
    return redirect('posts:post_detail', post_pk)