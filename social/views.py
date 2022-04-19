
import tweepy
from django.conf import settings
from allauth.socialaccount import app_settings, providers
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views import View
from .models import Post, Comment, UserProfile
from .forms import PostForm, CommentForm
from django.views.generic.edit import UpdateView, DeleteView

from allauth.socialaccount.models import SocialLogin, SocialToken, SocialApp
from allauth.socialaccount.providers.facebook.views import fb_complete_login
from allauth.socialaccount.helpers import complete_social_login
import allauth.account


def send(request, pk ):

    post = Post.objects.get(pk=pk)
    ki = SocialToken.objects.get(account=post.author.id-1)
    app = get_current_app(request, 'twitter')
    # Create Tweepy OAuth Handler
    oauth = tweepy.OAuthHandler(app.client_id, app.secret)
    # Retrieve access token from the current session, created by Allauth
    # access_key = request.session['oauth_%s_access_token' % 'api.twitter.com']['oauth_token']
    # access_secret = request.session['oauth_%s_access_token' % 'api.twitter.com']['oauth_token_secret']
    # Set access token in Tweepy OAuth Handler
    oauth.set_access_token(ki.token , ki.token_secret)
    # Return Tweepy API object
    # oauth.set_access_token(ACCESS_TOKEN1, ACCESS_TOKEN_SECRET1)

    api = tweepy.API(oauth)

    api.update_status(post.body)

    return render(request)


def get_current_app(request, provider):
	""" This chunk of code was borrowed from
		django-allauth/allauth/socialaccount/adapter.py
	:param request:
	:param provider:
	:return: app:
	"""
	from allauth.socialaccount.models import SocialApp

	config = app_settings.PROVIDERS.get(provider, {}).get('APP')
	if config:
		app = SocialApp(provider=provider)
		for field in ['client_id', 'secret', 'key']:
			setattr(app, field, config.get(field))
	else:
		app = SocialApp.objects.get_current(provider, request)
	return app


class PostListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.all().order_by('-created_on')
        form = PostForm()

        context = {
            'post_list': posts,
            'form': form,
        }

        return render(request, 'social/post_list.html', context)

    def post(self, request, *args, **kwargs):
        posts = Post.objects.all().order_by('-created_on')
        form = PostForm(request.POST)

        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()

        context = {
            'post_list': posts,
            'form': form,
        }

        return render(request, 'social/post_list.html', context)

class PostDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)
        ki = SocialToken.objects.get(account=post.author.id-1)
        form = CommentForm()

        comments = Comment.objects.filter(post=post).order_by('-created_on')

        context = {
            'ki':ki,
            'post': post,
            'form': form,
            'comments': comments,

        }

        return render(request, 'social/post_detail.html', context)
    def post(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)
        form = CommentForm(request.POST)

        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author = request.user
            new_comment.post = post
            new_comment.save()

        comments = Comment.objects.filter(post=post).order_by('-created_on')

        context = {
            'post': post,
            'form': form,
            'comments': comments,
        }

        return render(request, 'social/post_detail.html', context)

class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['body']
    template_name = 'social/post_edit.html'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy('post-detail', kwargs={'pk': pk})

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'social/post_delete.html'
    success_url = reverse_lazy('post-list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'social/comment_delete.html'

    def get_success_url(self):
        pk = self.kwargs['post_pk']
        return reverse_lazy('post-detail', kwargs={'pk': pk})

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class ProfileView(View):
    def get(self, request, pk, *args, **kwargs):
        profile = UserProfile.objects.get(pk=pk)
        user = profile.user
        posts = Post.objects.filter(author=user).order_by('-created_on')

        context = {
            'user': user,
            'profile': profile,
            'posts': posts
        }

        return render(request, 'social/profile.html', context)

class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserProfile
    fields = ['name', 'bio', 'birth_date', 'location', 'picture']
    template_name = 'social/profile_edit.html'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy('profile', kwargs={'pk': pk})

    def test_func(self):
        profile = self.get_object()
        return self.request.user == profile.user

# /////////////////

##

def sendF(request, pk ):
    post = Post.objects.get(pk=pk)
    ki = SocialToken.objects.get(account=post.author.id-1)
    access_token =  SocialToken.objects.get(account=post.author.id-1, account__provider='facebook')
    # post.body
    r = requests.get('https://graph.facebook.com/me?access_token='+access_token.token+'&fields=id,name,email')
