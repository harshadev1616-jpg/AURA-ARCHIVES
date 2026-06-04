from django.shortcuts import render, get_object_or_404
from .models import BlogPost, BlogCategory


def blog_list(request):
    posts = BlogPost.objects.filter(status="published").select_related("author", "category")
    categories = BlogCategory.objects.all()
    return render(request, "blog/list.html", {"posts": posts, "categories": categories})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status="published")
    post.view_count += 1
    post.save(update_fields=["view_count"])
    related = BlogPost.objects.filter(category=post.category, status="published").exclude(pk=post.pk)[:3]
    return render(request, "blog/detail.html", {"post": post, "related_posts": related})
