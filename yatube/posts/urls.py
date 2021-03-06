from django.urls import path

from . import views

urlpatterns = [
    path('404/', views.page_not_found),
    path('500/', views.server_error),
    path('', views.index,
         name='index'
         ),
    path('group/<slug:slug>/', views.group_posts,
         name='group_posts'
         ),
    path('new/', views.new_post,
         name='new_post'
         ),
    path('follow/', views.follow_index,
         name='follow_index'
         ),
    path('delete/post/<int:post_id>', views.delete_post,
         name='delete_post'
         ),
    path('delete/comment/<int:comment_id>', views.delete_comment,
         name='delete_comment'
         ),
    path('<str:username>/', views.profile,
         name='profile'
         ),
    path('<str:username>/follow/', views.profile_follow,
         name='profile_follow'
         ),
    path('<str:username>/unfollow/', views.profile_unfollow,
         name='profile_unfollow'
         ),
    path('<str:username>/<int:post_id>/', views.post_view,
         name='post'
         ),
    path('<username>/<int:post_id>/comment/', views.add_comment,
         name='add_comment'
         ),
    path('<str:username>/<int:post_id>/edit/', views.edit_post, name='edit')
]
