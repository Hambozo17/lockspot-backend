"""
LockSpot Admin Configuration
Enhanced Admin Dashboard with Charts and Analytics
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, LocationAddress, LockerLocation, PricingTier, LockerUnit,
    Discount, Booking, PaymentMethod, Payment, Review, 
    QRAccessCode, Notification, AuditLog
)


# ==================== USER ADMIN ====================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    
    list_display = ('email', 'full_name', 'phone', 'user_type', 'is_verified', 
                    'booking_count', 'total_spent', 'created_at')
    list_filter = ('user_type', 'is_verified', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'profile_image')
        }),
        ('Account Type', {
            'fields': ('user_type', 'is_verified')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2'),
        }),
    )
    
    def booking_count(self, obj):
        count = obj.bookings.count()
        if count > 0:
            url = reverse('admin:lockers_booking_changelist') + f'?user__id__exact={obj.id}'
            return format_html('<a href="{}">{} bookings</a>', url, count)
        return '0 bookings'
    booking_count.short_description = 'Bookings'
    
    def total_spent(self, obj):
        total = obj.bookings.filter(status='Completed').aggregate(
            total=Sum('total_amount'))['total'] or 0
        return format_html('<span style="color: green; font-weight: bold;">${}</span>', f"{total:.2f}")
    total_spent.short_description = 'Total Spent'


# ==================== LOCATION ADMIN ====================

class LockerInline(admin.TabularInline):
    """Inline display of lockers in location"""
    model = LockerUnit
    extra = 0
    fields = ('unit_number', 'size', 'status', 'tier')
    readonly_fields = ('qr_code',)
    show_change_link = True


@admin.register(LocationAddress)
class LocationAddressAdmin(admin.ModelAdmin):
    list_display = ('street_address', 'city', 'state', 'country', 'coordinates')
    list_filter = ('city', 'country')
    search_fields = ('street_address', 'city')
    
    def coordinates(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://maps.google.com/?q={},{}" target="_blank">📍 View Map</a>',
                obj.latitude, obj.longitude
            )
        return '-'
    coordinates.short_description = 'Location'


@admin.register(LockerLocation)
class LockerLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address_info', 'operating_hours', 'locker_stats', 
                    'status_badge', 'avg_rating')
    list_filter = ('is_active', 'address__city')
    search_fields = ('name', 'address__city', 'address__street_address')
    inlines = [LockerInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Location Details', {
            'fields': ('name', 'address', 'description', 'image')
        }),
        ('Operating Hours', {
            'fields': ('operating_hours_start', 'operating_hours_end', 'contact_phone')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def address_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color: #666;">{}</small>',
            obj.address.city, obj.address.street_address
        )
    address_info.short_description = 'Address'
    
    def operating_hours(self, obj):
        return f"{obj.operating_hours_start.strftime('%H:%M')} - {obj.operating_hours_end.strftime('%H:%M')}"
    operating_hours.short_description = 'Hours'
    
    def locker_stats(self, obj):
        available = obj.available_lockers_count
        total = obj.total_lockers_count
        if total == 0:
            return 'No lockers'
        percentage = (available / total) * 100
        color = 'green' if percentage > 50 else 'orange' if percentage > 20 else 'red'
        return format_html(
            '<span style="color: {};">{}/{} available ({}%)</span>',
            color, available, total, f"{percentage:.0f}"
        )
    locker_stats.short_description = 'Lockers'
    
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px;">Active</span>')
        return format_html('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px;">Inactive</span>')
    status_badge.short_description = 'Status'
    
    def avg_rating(self, obj):
        rating = obj.average_rating
        if rating:
            stars = '★' * int(rating) + '☆' * (5 - int(rating))
            return format_html('<span style="color: #ffc107;">{}</span> ({})', stars, f"{rating:.1f}")
        return 'No ratings'
    avg_rating.short_description = 'Rating'


# ==================== PRICING ADMIN ====================

@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'size', 'display_pricing', 'locker_count', 'is_active')
    list_filter = ('size', 'is_active')
    search_fields = ('name',)
    
    def display_pricing(self, obj):
        return format_html(
            '<div style="line-height: 1.4;">'
            '<small>Hourly:</small> <strong>${}</strong><br>'
            '<small>Daily:</small> <strong>${}</strong><br>'
            '<small>Weekly:</small> <strong>${}</strong>'
            '</div>',
            obj.hourly_rate, obj.daily_rate, obj.weekly_rate or '-'
        )
    display_pricing.short_description = 'Pricing'
    
    def locker_count(self, obj):
        return obj.lockers.count()
    locker_count.short_description = 'Units'


# ==================== LOCKER ADMIN ====================

@admin.register(LockerUnit)
class LockerUnitAdmin(admin.ModelAdmin):
    list_display = ('display_locker', 'location', 'size', 'status_badge', 
                    'tier', 'last_maintenance', 'booking_status')
    list_filter = ('status', 'size', 'location', 'location__address__city')
    search_fields = ('unit_number', 'location__name')
    list_per_page = 50
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_available', 'mark_maintenance', 'mark_out_of_service']
    
    def display_locker(self, obj):
        return format_html(
            '<strong style="font-size: 14px;">#{}</strong>',
            obj.unit_number
        )
    display_locker.short_description = 'Unit'
    
    def status_badge(self, obj):
        colors = {
            'Available': '#28a745',
            'Booked': '#007bff',
            'Maintenance': '#ffc107',
            'OutOfService': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def last_maintenance(self, obj):
        if obj.last_maintenance_date:
            days_ago = (timezone.now().date() - obj.last_maintenance_date).days
            if days_ago > 30:
                return format_html('<span style="color: red;">{} days ago</span>', days_ago)
            return f'{days_ago} days ago'
        return format_html('<span style="color: orange;">Never</span>')
    last_maintenance.short_description = 'Maintenance'
    
    def booking_status(self, obj):
        active_booking = obj.bookings.filter(status__in=['Confirmed', 'Active']).first()
        if active_booking:
            return format_html(
                '<a href="{}" style="color: #007bff;">Booking #{}</a>',
                reverse('admin:lockers_booking_change', args=[active_booking.id]),
                active_booking.id
            )
        return '-'
    booking_status.short_description = 'Current Booking'
    
    @admin.action(description='Mark selected as Available')
    def mark_available(self, request, queryset):
        queryset.update(status='Available')
    
    @admin.action(description='Mark selected as Under Maintenance')
    def mark_maintenance(self, request, queryset):
        queryset.update(status='Maintenance', last_maintenance_date=timezone.now().date())
    
    @admin.action(description='Mark selected as Out of Service')
    def mark_out_of_service(self, request, queryset):
        queryset.update(status='OutOfService')


# ==================== BOOKING ADMIN ====================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer_info', 'locker_info', 'booking_period',
                    'duration', 'amount_display', 'status_badge', 'created_at')
    list_filter = ('status', 'booking_type', 'created_at', 'locker__location')
    search_fields = ('id', 'user__email', 'user__first_name', 'locker__location__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'duration_hours')
    list_per_page = 25
    actions = ['confirm_bookings', 'complete_bookings', 'cancel_bookings']
    
    fieldsets = (
        ('Booking Info', {
            'fields': ('user', 'locker', 'booking_type', 'status')
        }),
        ('Time Period', {
            'fields': ('start_time', 'end_time')
        }),
        ('Pricing', {
            'fields': ('subtotal_amount', 'discount', 'discount_amount', 'total_amount')
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def booking_id(self, obj):
        return format_html('<strong style="font-size: 13px;">#{}</strong>', obj.id)
    booking_id.short_description = 'ID'
    
    def customer_info(self, obj):
        return format_html(
            '<div>'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            obj.user.full_name, obj.user.email
        )
    customer_info.short_description = 'Customer'
    
    def locker_info(self, obj):
        return format_html(
            '<div>'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">Unit {} ({})</small>'
            '</div>',
            obj.locker.location.name, obj.locker.unit_number, obj.locker.size
        )
    locker_info.short_description = 'Locker'
    
    def booking_period(self, obj):
        return format_html(
            '<div style="font-size: 12px;">'
            '<strong>{}</strong><br>'
            'to<br>'
            '<strong>{}</strong>'
            '</div>',
            obj.start_time.strftime('%b %d, %H:%M'),
            obj.end_time.strftime('%b %d, %H:%M')
        )
    booking_period.short_description = 'Period'
    
    def duration(self, obj):
        hours = obj.duration_hours
        if hours < 24:
            return f'{hours:.1f}h'
        days = hours / 24
        return f'{days:.1f}d'
    duration.short_description = 'Duration'
    
    def amount_display(self, obj):
        discount_info = ''
        if obj.discount_amount > 0:
            discount_info = format_html(' <small style="color: green;">(-${})</small>', obj.discount_amount)
        return format_html(
            '<strong style="color: #28a745; font-size: 14px;">${}</strong>{}',
            obj.total_amount, discount_info
        )
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'Pending': '#ffc107',
            'Confirmed': '#17a2b8',
            'Active': '#28a745',
            'Completed': '#6c757d',
            'Cancelled': '#dc3545',
            'Expired': '#343a40'
        }
        color = colors.get(obj.status, '#6c757d')
        text_color = 'black' if obj.status == 'Pending' else 'white'
        return format_html(
            '<span style="background: {}; color: {}; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color, text_color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    @admin.action(description='Confirm selected bookings')
    def confirm_bookings(self, request, queryset):
        queryset.filter(status='Pending').update(status='Confirmed')
    
    @admin.action(description='Mark as Completed')
    def complete_bookings(self, request, queryset):
        queryset.filter(status__in=['Confirmed', 'Active']).update(status='Completed')
    
    @admin.action(description='Cancel selected bookings')
    def cancel_bookings(self, request, queryset):
        queryset.exclude(status__in=['Completed', 'Cancelled']).update(status='Cancelled')


# ==================== DISCOUNT ADMIN ====================

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_display', 'usage_stats', 'validity_period', 
                    'status_badge', 'revenue_impact')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'description')
    readonly_fields = ('current_uses', 'created_at')
    
    def discount_display(self, obj):
        if obj.discount_type == 'Percentage':
            return format_html('<strong style="color: #e83e8c; font-size: 16px;">{}%</strong> OFF', obj.discount_value)
        return format_html('<strong style="color: #e83e8c; font-size: 16px;">${}</strong> OFF', obj.discount_value)
    discount_display.short_description = 'Discount'
    
    def usage_stats(self, obj):
        if obj.max_uses:
            percentage = (obj.current_uses / obj.max_uses) * 100
            return format_html(
                '<div style="width: 80px;">'
                '<div style="background: #e9ecef; border-radius: 4px;">'
                '<div style="background: #007bff; width: {}%; height: 6px; border-radius: 4px;"></div>'
                '</div>'
                '<small>{}/{}</small>'
                '</div>',
                percentage, obj.current_uses, obj.max_uses
            )
        return f'{obj.current_uses} uses'
    usage_stats.short_description = 'Usage'
    
    def validity_period(self, obj):
        now = timezone.now()
        if now < obj.valid_from:
            return format_html('<span style="color: orange;">Starts {}</span>', obj.valid_from.strftime('%b %d'))
        if now > obj.valid_to:
            return format_html('<span style="color: red;">Expired</span>')
        days_left = (obj.valid_to - now).days
        return format_html('<span style="color: green;">{} days left</span>', days_left)
    validity_period.short_description = 'Validity'
    
    def status_badge(self, obj):
        if obj.is_valid:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px;">Valid</span>')
        return format_html('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px;">Invalid</span>')
    status_badge.short_description = 'Status'
    
    def revenue_impact(self, obj):
        total = obj.bookings.aggregate(total=Sum('discount_amount'))['total'] or 0
        return format_html('<span style="color: #dc3545;">-${}</span>', f"{total:.2f}")
    revenue_impact.short_description = 'Total Discounted'


# ==================== PAYMENT ADMIN ====================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'booking_link', 'amount_display', 'method_info',
                    'status_badge', 'payment_date')
    list_filter = ('status', 'payment_date')
    search_fields = ('transaction_reference', 'booking__user__email')
    date_hierarchy = 'payment_date'
    readonly_fields = ('payment_date',)
    
    def payment_id(self, obj):
        return format_html('<strong>#{}</strong>', obj.id)
    payment_id.short_description = 'ID'
    
    def booking_link(self, obj):
        return format_html(
            '<a href="{}">Booking #{}</a>',
            reverse('admin:lockers_booking_change', args=[obj.booking.id]),
            obj.booking.id
        )
    booking_link.short_description = 'Booking'
    
    def amount_display(self, obj):
        return format_html('<strong style="color: #28a745; font-size: 14px;">${}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def method_info(self, obj):
        if obj.method:
            return str(obj.method)
        return 'N/A'
    method_info.short_description = 'Method'
    
    def status_badge(self, obj):
        colors = {
            'Pending': '#ffc107',
            'Success': '#28a745',
            'Failed': '#dc3545',
            'Refunded': '#17a2b8',
            'PartialRefund': '#6f42c1'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ==================== REVIEW ADMIN ====================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'customer', 'location', 'rating_display', 
                    'comment_preview', 'created_at')
    list_filter = ('rating', 'is_verified', 'created_at')
    search_fields = ('booking__user__email', 'title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    
    def review_id(self, obj):
        return format_html('<strong>#{}</strong>', obj.id)
    review_id.short_description = 'ID'
    
    def customer(self, obj):
        return obj.booking.user.full_name
    customer.short_description = 'Customer'
    
    def location(self, obj):
        return obj.booking.locker.location.name
    location.short_description = 'Location'
    
    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        colors = {1: '#dc3545', 2: '#fd7e14', 3: '#ffc107', 4: '#28a745', 5: '#20c997'}
        return format_html('<span style="color: {}; font-size: 16px;">{}</span>', colors[obj.rating], stars)
    rating_display.short_description = 'Rating'
    
    def comment_preview(self, obj):
        if obj.comment:
            preview = obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
            return preview
        return '-'
    comment_preview.short_description = 'Comment'


# ==================== NOTIFICATION ADMIN ====================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'read_status', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    
    def read_status(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        return format_html('<span style="color: orange;">● Unread</span>')
    read_status.short_description = 'Status'


# ==================== AUDIT LOG ADMIN ====================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'table_name', 'record_id', 'ip_address', 'created_at')
    list_filter = ('action', 'table_name', 'created_at')
    search_fields = ('action', 'user__email')
    readonly_fields = ('user', 'action', 'table_name', 'record_id', 'old_values', 
                       'new_values', 'ip_address', 'user_agent', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ==================== PAYMENT METHOD ADMIN ====================

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'card_display', 'is_default', 'is_active')
    list_filter = ('method_type', 'is_default', 'is_active')
    search_fields = ('user__email',)
    
    def card_display(self, obj):
        if obj.card_last_four:
            return f'****{obj.card_last_four}'
        return '-'
    card_display.short_description = 'Card'


# ==================== QR CODE ADMIN ====================

@admin.register(QRAccessCode)
class QRAccessCodeAdmin(admin.ModelAdmin):
    list_display = ('code_display', 'booking', 'code_type', 'usage_status', 
                    'expires_at', 'is_used')
    list_filter = ('code_type', 'is_used')
    search_fields = ('code', 'booking__id')
    
    def code_display(self, obj):
        return format_html('<code style="background: #f8f9fa; padding: 2px 6px; border-radius: 4px;">{}</code>', obj.code[:20] + '...')
    code_display.short_description = 'Code'
    
    def usage_status(self, obj):
        if obj.is_used:
            return format_html('<span style="color: green;">✓ Used at {}</span>', obj.used_at.strftime('%H:%M'))
        if obj.expires_at < timezone.now():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: orange;">Active</span>')
    usage_status.short_description = 'Status'


# ==================== ADMIN SITE CONFIG ====================

admin.site.site_header = 'LockSpot Administration'
admin.site.site_title = 'LockSpot Admin'
admin.site.index_title = 'Dashboard'
