"""
LockSpot Django Models - Smart Locker Booking System
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# ==================== CUSTOM USER ====================

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'Admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User Model for LockSpot"""
    
    class UserType(models.TextChoices):
        CUSTOMER = 'Customer', 'Customer'
        ADMIN = 'Admin', 'Admin'
    
    username = None  # Remove username field
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, null=True, blank=True)  # Nullable, not unique
    user_type = models.CharField(max_length=10, choices=UserType.choices, default=UserType.CUSTOMER)
    is_verified = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']
    
    class Meta:
        db_table = 'lockers_user'  # Match actual table name
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# ==================== LOCATION MODELS ====================

class LocationAddress(models.Model):
    """Address for locker locations"""
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=50, default='Saudi Arabia')
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Location Address'
        verbose_name_plural = 'Location Addresses'
    
    def __str__(self):
        return f"{self.street_address}, {self.city}"


class LockerLocation(models.Model):
    """Locker station/location"""
    name = models.CharField(max_length=100, unique=True)
    address = models.ForeignKey(LocationAddress, on_delete=models.PROTECT, related_name='locations')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='locations/', null=True, blank=True)
    operating_hours_start = models.TimeField(default='08:00:00')
    operating_hours_end = models.TimeField(default='22:00:00')
    is_active = models.BooleanField(default=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Locker Location'
        verbose_name_plural = 'Locker Locations'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def available_lockers_count(self):
        return self.lockers.filter(status='Available').count()
    
    @property
    def total_lockers_count(self):
        return self.lockers.count()
    
    @property
    def average_rating(self):
        from django.db.models import Avg
        avg = Booking.objects.filter(
            locker__location=self, 
            review__isnull=False
        ).aggregate(avg_rating=Avg('review__rating'))
        return avg['avg_rating'] or 0


# ==================== PRICING & LOCKER MODELS ====================

class PricingTier(models.Model):
    """Pricing configuration for lockers"""
    
    class LockerSize(models.TextChoices):
        SMALL = 'Small', 'Small (Bags, Laptops)'
        MEDIUM = 'Medium', 'Medium (Suitcases)'
        LARGE = 'Large', 'Large (Sports Equipment)'
    
    name = models.CharField(max_length=50)
    size = models.CharField(max_length=10, choices=LockerSize.choices)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    weekly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pricing Tier'
        verbose_name_plural = 'Pricing Tiers'
        unique_together = ['name', 'size']
    
    def __str__(self):
        return f"{self.name} - {self.size} (${self.hourly_rate}/hr)"


class LockerUnit(models.Model):
    """Individual locker boxes"""
    
    class Status(models.TextChoices):
        AVAILABLE = 'Available', 'Available'
        BOOKED = 'Booked', 'Booked'
        MAINTENANCE = 'Maintenance', 'Under Maintenance'
        OUT_OF_SERVICE = 'OutOfService', 'Out of Service'
    
    class Size(models.TextChoices):
        SMALL = 'Small', 'Small'
        MEDIUM = 'Medium', 'Medium'
        LARGE = 'Large', 'Large'
    
    location = models.ForeignKey(LockerLocation, on_delete=models.CASCADE, related_name='lockers')
    tier = models.ForeignKey(PricingTier, on_delete=models.PROTECT, related_name='lockers')
    unit_number = models.CharField(max_length=10)
    size = models.CharField(max_length=10, choices=Size.choices)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.AVAILABLE)
    qr_code = models.CharField(max_length=255, unique=True, null=True, blank=True)
    last_maintenance_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Locker Unit'
        verbose_name_plural = 'Locker Units'
        unique_together = ['location', 'unit_number']
        ordering = ['location', 'unit_number']
    
    def __str__(self):
        return f"{self.location.name} - Unit {self.unit_number} ({self.size})"


# ==================== DISCOUNT MODEL ====================

class Discount(models.Model):
    """Discount/Promo codes"""
    
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'Percentage', 'Percentage'
        FIXED_AMOUNT = 'FixedAmount', 'Fixed Amount'
    
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    discount_type = models.CharField(max_length=15, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_booking_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.IntegerField(null=True, blank=True)
    current_uses = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Discount'
        verbose_name_plural = 'Discounts'
    
    def __str__(self):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return f"{self.code} ({self.discount_value}% OFF)"
        return f"{self.code} (${self.discount_value} OFF)"
    
    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_to:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True


# ==================== BOOKING MODEL ====================

class Booking(models.Model):
    """Main booking/reservation table"""
    
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        CONFIRMED = 'Confirmed', 'Confirmed'
        ACTIVE = 'Active', 'Active'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'
        EXPIRED = 'Expired', 'Expired'
    
    class BookingType(models.TextChoices):
        STORAGE = 'Storage', 'Storage'
        DELIVERY = 'Delivery', 'Delivery'
    
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bookings')
    locker = models.ForeignKey(LockerUnit, on_delete=models.PROTECT, related_name='bookings')
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    booking_type = models.CharField(max_length=10, choices=BookingType.choices, default=BookingType.STORAGE)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    cancellation_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking #{self.id} - {self.user.email} at {self.locker.location.name}"
    
    @property
    def duration_hours(self):
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600


# ==================== PAYMENT MODELS ====================

class PaymentMethod(models.Model):
    """Saved payment methods for users"""
    
    class MethodType(models.TextChoices):
        VISA = 'Visa', 'Visa'
        MASTERCARD = 'Mastercard', 'Mastercard'
        MOBILE_WALLET = 'MobileWallet', 'Mobile Wallet'
        CASH = 'Cash', 'Cash'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=15, choices=MethodType.choices)
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    card_holder_name = models.CharField(max_length=100, blank=True, null=True)
    expiry_month = models.PositiveSmallIntegerField(null=True, blank=True)
    expiry_year = models.PositiveSmallIntegerField(null=True, blank=True)
    wallet_phone = models.CharField(max_length=20, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def __str__(self):
        if self.card_last_four:
            return f"{self.method_type} ****{self.card_last_four}"
        return f"{self.method_type}"


class Payment(models.Model):
    """Payment transactions"""
    
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        SUCCESS = 'Success', 'Success'
        FAILED = 'Failed', 'Failed'
        REFUNDED = 'Refunded', 'Refunded'
        PARTIAL_REFUND = 'PartialRefund', 'Partial Refund'
    
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name='payment')
    method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment #{self.id} - ${self.amount} ({self.status})"


# ==================== REVIEW MODEL ====================

class Review(models.Model):
    """User reviews for bookings"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=100, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.booking.user.email} - {self.rating}★"


# ==================== QR ACCESS CODE ====================

class QRAccessCode(models.Model):
    """QR codes for locker access"""
    
    class CodeType(models.TextChoices):
        UNLOCK = 'Unlock', 'Unlock'
        LOCK = 'Lock', 'Lock'
        EMERGENCY = 'Emergency', 'Emergency'
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='qr_codes')
    code = models.CharField(max_length=255, unique=True)
    code_type = models.CharField(max_length=15, choices=CodeType.choices, default=CodeType.UNLOCK)
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'QR Access Code'
        verbose_name_plural = 'QR Access Codes'
    
    def __str__(self):
        return f"QR {self.code_type} for Booking #{self.booking.id}"


# ==================== NOTIFICATION MODEL ====================

class Notification(models.Model):
    """User notifications"""
    
    class NotificationType(models.TextChoices):
        BOOKING = 'Booking', 'Booking'
        PAYMENT = 'Payment', 'Payment'
        REMINDER = 'Reminder', 'Reminder'
        PROMO = 'Promo', 'Promotional'
        SYSTEM = 'System', 'System'
        SECURITY = 'Security', 'Security'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=15, choices=NotificationType.choices)
    related_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type}: {self.title}"


# ==================== AUDIT LOG ====================

class AuditLog(models.Model):
    """System audit trail"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    table_name = models.CharField(max_length=50, blank=True, null=True)
    record_id = models.IntegerField(null=True, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} by {self.user or 'System'}"
