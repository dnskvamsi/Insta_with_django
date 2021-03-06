from django.shortcuts import redirect, render
from django.http import HttpResponse
from . import forms
from .forms import LoginForm, PostForm
from instagramapp.models import Comments, SubComments, Users, Post, Follow, Comments
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from datetime import datetime
from django.db.models import Q, Sum

global search_for_user
search_for_user = ""

# Create your views here.
def signup_page(request):
    if request.session.has_key("user"):
        del request.session["user"]
    form = forms.UserForm
    if request.method == "POST":
        form = forms.UserForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            request.session["user"] = form.cleaned_data["user_name"]
            request.session["obj"] = Users.objects.get(
                user_name=request.session["user"]
            ).profile_pic.url
            return redirect("/home")
        else:
            return render(request, "instagramapp/sign-up.html", {"form": form})
        # return render(request, "instagramapp/sign-up.html", {"form": form})
    return render(request, "instagramapp/sign-up.html", {"form": form})


def view_login(request):
    if request.session.has_key("user"):
        del request.session["user"]
    err = ""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user_name = form.cleaned_data["user_name"]
            password = form.cleaned_data["password"]
            user = Users.objects.get(user_name=user_name)

            if user:
                # print(user)
                if user.password == password:
                    request.session["user"] = user.user_name
                    request.session["obj"] = Users.objects.get(
                        user_name=request.session["user"]
                    ).profile_pic.url
                    print(request.session["obj"])
                    return redirect("/home")
                else:
                    err = "Password Mismatch"
        else:
            return render(request, "instagramapp/login.html", {"form": form})

    else:
        form = LoginForm()
    return render(request, "instagramapp/login.html", {"form": form, "err": err})


def view_home(request):
    if request.session.has_key("user"):
        session_user_name = request.session["user"]
        session_user_object = Users.objects.get(user_name=session_user_name)
        session_user_following, create = Follow.objects.get_or_create(
            user=session_user_object
        )
        following = session_user_following.following.all()
        posts = Post.objects.filter(user__in=following).order_by("-created")
        users = Users.objects.exclude(user_name=session_user_name)
        print(request.session["obj"])
        if request.method == "POST":
            pk = request.POST.get("post_pk")
            post_obj = Post.objects.get(pk=pk)
            if session_user_object in post_obj.likes.all():
                post_obj.likes.remove(session_user_object)
            else:
                post_obj.likes.add(session_user_object)
        return render(
            request,
            "instagramapp/profile-home.html",
            {
                "posts": posts,
                "session_user": session_user_object,
                "users": users,
                "following": following,
            },
        )
    else:
        return redirect("/login")


def view_profile(request, user_name):
    today_date = datetime.now()
    if request.session.has_key("user"):
        session_user_name = request.session["user"]
        # user = Users.objects.get(user_name=session_user_name)
        my_posts = Post.objects.filter(user=user_name)
        session_user_object = Users.objects.get(user_name=session_user_name)
        session_user_following = Follow.objects.get(user=session_user_object)
        session_user_following_members = session_user_following.following.all()
        following_count = (
            Follow.objects.get(user__user_name=user_name).following.all().count()
        )
        name = Users.objects.get(user_name=user_name).name
        followers_count = Users.objects.get(user_name=user_name).followers.all().count()
        if request.method == "POST":
            pass
        user_info = {
            "my_posts": my_posts,
            "user_name": user_name,
            "count_of_posts": len(my_posts),
            "following_count": following_count,
            "followers_count": followers_count,
            "name": name,
            "session_user_following": session_user_following_members,
            "user_obj": Users.objects.get(user_name=user_name),
        }
        return render(request, "instagramapp/profile.html", context=user_info)
    else:
        return redirect("/login")


def post(request):
    if request.session.has_key("user"):
        user_name = request.session["user"]
        if request.method == "POST":
            form = forms.PostForm(request.POST, request.FILES)
            if form.is_valid():
                post = form.cleaned_data.get("post")
                location = form.cleaned_data.get("location")
                description = form.cleaned_data.get("description")
                user = Users.objects.get(user_name=user_name)
                obj = Post(
                    user=user, post=post, location=location, description=description
                )
                obj.save()
            return redirect("/profile/" + user_name)
            # else:
            #     return render(request, "instagramapp/post-form.html")
        else:
            form = forms.PostForm()
        return render(request, "instagramapp/post-form.html", {"form": form})
    else:
        return redirect("/login")


def follow_user(request, user_name):
    if request.session.has_key("user"):
        session_user = request.session["user"]
        session_user_obj = Users.objects.get(user_name=session_user)
        user_exists = Follow.objects.filter(user=session_user_obj).exists()
        follow = Users.objects.get(user_name=user_name)
        if user_exists:
            to_follow = Follow.objects.get(user=session_user_obj)
            to_follow.following.add(follow)
        else:
            Follow.objects.create(user=session_user_obj)
            to_follow = Follow.objects.get(user=session_user_obj)
            to_follow.following.add(follow)
        if request.method == "POST":
            next = request.POST.get("next", "/")
            return HttpResponseRedirect(next)
        return redirect("/home")
    else:
        return redirect("/login")


def unfollow(request, user_name):
    if request.session.has_key("user"):
        session_user = request.session["user"]
        session_user_obj = Users.objects.get(user_name=session_user)
        unfollow_user = Users.objects.get(user_name=user_name)
        session_user_following_info = Follow.objects.get(user=session_user_obj)
        session_user_following_info.following.remove(unfollow_user)
        if request.method == "POST":
            next = request.POST.get("next", "/")
            return HttpResponseRedirect(next)
        return redirect("/home")
    else:
        return render("/login")


def explore(request):
    if request.session.has_key("user"):
        current_user = request.session["user"]
        current_user_obj = Users.objects.get(user_name=current_user)
        following = Follow.objects.filter(user=current_user_obj).values("following")
        posts = Post.objects.exclude(user__user_name=current_user).order_by("-created")
        if following[0]["following"] is not None:
            others = Users.objects.exclude(user_name__in=following).exclude(
                user_name=current_user
            )
        else:
            others = Users.objects.exclude(user_name=current_user)
        following_user_objects = Follow.objects.get(
            user__user_name=current_user
        ).following.all()

        ## if we get a like or un-like request

        if request.method == "POST":
            pk = request.POST.get("post_pk")
            post_obj = Post.objects.get(pk=pk)
            if current_user_obj in post_obj.likes.all():
                post_obj.likes.remove(current_user_obj)
            else:
                post_obj.likes.add(current_user_obj)

        return render(
            request,
            "instagramapp/explore-friends.html",
            context={
                "following": following,
                "others": others,
                "posts": posts,
                "following_user_objects": following_user_objects,
                "session_user": current_user_obj,
            },
        )
    else:
        return redirect("/login")


def delete_post(request, pk):
    session_user = request.session["user"]
    # if request.method == "POST":
    post = Post.objects.get(id=pk)
    post.delete()
    return redirect(f"/profile/{session_user}")


def view_post(request, pk):
    today_date = datetime.now()
    session_user = request.session["user"]
    session_user_obj = Users.objects.get(user_name=session_user)
    post = Post.objects.get(pk=pk)
    related_post_user_obj = post.user
    related_posts = Post.objects.filter(user=related_post_user_obj).exclude(pk=post.pk)
    following = Follow.objects.get(user__user_name=session_user).following.all()
    ## For like -dislike function
    comments = Comments.objects.filter(post__pk=pk)

    if request.method == "POST":
        pk = request.POST.get("post_pk")
        post_obj = Post.objects.get(pk=pk)
        if session_user_obj in post_obj.likes.all():
            post_obj.likes.remove(session_user_obj)
        else:
            post_obj.likes.add(session_user_obj)
    return render(
        request,
        "instagramapp/view-post.html",
        {
            "post": post,
            "session_user": session_user_obj,
            "related_posts": related_posts,
            "following": following,
            "today_date": today_date,
            "comments": comments,
        },
    )


def delete_account(request, user_name):
    Users.objects.filter(user_name=user_name).delete()
    return redirect("/sign-up")


def like_post(request, pk):
    user_name = request.session["user"]
    pk = request.POST.get("post_pk")
    post_obj = Post.objects.get(pk=pk)
    session_user_obj = Users.objects.get(user_name=user_name)
    if session_user_obj in post_obj.likes.all():
        post_obj.likes.remove(session_user_obj)
    else:
        post_obj.likes.add(session_user_obj)
    # likes_count = post_obj.likes.count()
    # context = {"count": likes_count}
    return redirect("/home")


def view_followers(request, user_name):
    user_obj = Users.objects.get(user_name=user_name)
    followers = user_obj.followers.all()
    following = Follow.objects.get(
        user__user_name=request.session["user"]
    ).following.all()
    return render(
        request,
        "instagramapp/view-followers.html",
        {"followers": followers, "following": following},
    )


def view_following(request, user_name):
    following = Follow.objects.get(user__user_name=user_name).following.all()
    print(following)
    session_user_following = Follow.objects.get(
        user__user_name=request.session["user"]
    ).following.all()
    return render(
        request,
        "instagramapp/view-following.html",
        {"following": following, "session_user_following": session_user_following},
    )


def search_user(request):
    global search_for_user
    session_user = request.session["user"]
    if request.method == "POST":
        search_for_user = request.POST.get("search")
        search_for_user = search_for_user.strip()
        if search_for_user != "":
            search_results = Users.objects.filter(
                Q(user_name__icontains=search_for_user)
                | Q(name__icontains=search_for_user)
            ).exclude(user_name=session_user)
            session_user_following = Follow.objects.get(
                user__user_name=session_user
            ).following.all()
            context = {
                "session_user_following": session_user_following,
                "search_results": search_results,
                "search_for_user": search_for_user,
            }
            return render(request, "instagramapp/search-page.html", context)
        else:
            return redirect("/home")
    else:
        if search_for_user != "":
            search_results = Users.objects.filter(
                Q(user_name__contains=search_for_user)
                | Q(name__contains=search_for_user)
            ).exclude(user_name=session_user)
            session_user_following = Follow.objects.get(
                user__user_name=session_user
            ).following.all()
            context = {
                "session_user_following": session_user_following,
                "search_results": search_results,
                "search_for_user": search_for_user,
            }
        return render(request, "instagramapp/search-page.html", context)
    return redirect("/search")


def add_comment(request, pk):
    session_user = request.session["user"]
    session_user_obj = Users.objects.get(user_name=session_user)
    post = Post.objects.get(pk=pk)
    if request.method == "POST":
        comment = request.POST.get("comment")
        Comments.objects.create(post=post, user=session_user_obj, comment=comment)
        return redirect("/viewpost/" + str(pk))
    return redirect("/viewpost/" + str(pk))


def update_profile(request):
    session_user_obj = Users.objects.get(user_name=request.session["user"])
    err = ""
    if request.method == "POST":
        image = request.FILES.get("profile_pic", None)
        # user_name = request.POST.get("user-name")
        name = request.POST.get("name")
        email = request.POST.get("email")
        # print(email)
        if name.strip() != "":
            session_user_obj.name = name
        if email.strip() != "":
            if Users.objects.filter(email=email):
                err = "Email already taken"
            else:
                session_user_obj.email = email
        if image:
            session_user_obj.profile_pic = image
        if err:
            # print("error", err)
            return render(
                request,
                "instagramapp/update-profile.html",
                {"user": session_user_obj, "err": err},
            )
        else:
            session_user_obj.save()
            request.session["obj"] = session_user_obj.profile_pic.url
            return redirect(f"/profile/{session_user_obj.user_name}")

    return render(
        request,
        "instagramapp/update-profile.html",
        {"user": session_user_obj, "err": err},
    )


def add_sub_comments(request, pk):
    session_user = request.session["user"]
    session_user_obj = Users.objects.get(user_name=session_user)
    # post = Post.objects.get(pk=pk)
    if request.method == "POST":
        comment_id = request.POST.get("comment-pk")
        comment = request.POST.get("comment")
        comment_obj = Comments.objects.get(pk=comment_id)
        SubComments.objects.create(
            comment_id=comment_obj, comment=comment, user=session_user_obj
        )
        # Comments.objects.create(post=post, user=session_user_obj, comment=comment)
        return redirect("/viewpost/" + str(pk))

    return redirect("/viewpost/" + str(pk))
