"""
API URL Configuration - 100% Raw SQL Implementation
No Django ORM ViewSets
"""

from django.urls import path
from .views import (
    # Auth
    RegisterView, LoginView, ProfileView,
    # Locations
    LocationListView, LocationDetailView, LocationPricingView,
    # Lockers
    LockerListView, LockerAvailabilityView,
    # Bookings
    BookingListCreateView, BookingDetailView, BookingQRView, BookingCancelView,
    # Reviews
    ReviewListCreateView, LocationReviewsView,
    # Notifications
    NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView,
    # Discounts
    DiscountView,
    # Health
    health_check
)

urlpatterns = [
    # Health Check
    path('', health_check, name='health'),
    path('health/', health_check, name='health_check'),
    
    # ==================== AUTH ====================
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', ProfileView.as_view(), name='profile'),
    
    # ==================== LOCATIONS ====================
    path('locations/', LocationListView.as_view(), name='location-list'),
    path('locations/<int:location_id>/', LocationDetailView.as_view(), name='location-detail'),
    path('locations/<int:location_id>/pricing/', LocationPricingView.as_view(), name='location-pricing'),
    path('locations/<int:location_id>/reviews/', LocationReviewsView.as_view(), name='location-reviews'),
    
    # ==================== LOCKERS ====================
    path('lockers/', LockerListView.as_view(), name='locker-list'),
    path('lockers/available/', LockerListView.as_view(), name='locker-available'),  # Alias for Flutter app
    path('lockers/<int:locker_id>/availability/', LockerAvailabilityView.as_view(), name='locker-availability'),
    
    # ==================== BOOKINGS ====================
    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<int:booking_id>/', BookingDetailView.as_view(), name='booking-detail'),
    path('bookings/<int:booking_id>/qr/', BookingQRView.as_view(), name='booking-qr'),
    path('bookings/<int:booking_id>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
    
    # ==================== REVIEWS ====================
    path('reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    
    # ==================== NOTIFICATIONS ====================
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('notifications/read-all/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    
    # ==================== DISCOUNTS ====================
    path('discounts/validate/', DiscountView.as_view(), name='discount-validate'),
]
