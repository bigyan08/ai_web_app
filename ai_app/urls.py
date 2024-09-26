from . import views
from django.urls import path

urlpatterns=[
    path('',views.index, name="index"),
    path('login/',views.user_login,name="login"),
    path('signup/',views.user_signup,name="signup"),
    path('logout/',views.user_logout,name="logout"),
]