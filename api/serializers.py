"""
API Serializers for LockSpot
"""

from rest_framework import serializers
from lockers.models import (
    User, LocationAddress, LockerLocation, PricingTier, LockerUnit,
    Discount, Booking, PaymentMethod, Payment, Review, QRAccessCode, Notification
)


# ==================== USER SERIALIZERS ====================

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'password')
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    user_id = serializers.IntegerField(source='id', read_only=True)
    
    class Meta:
        model = User
        fields = ('user_id', 'id', 'email', 'first_name', 'last_name', 'full_name', 
                  'phone', 'user_type', 'is_verified', 'profile_image', 'created_at')
        read_only_fields = ('id', 'user_id', 'user_type', 'is_verified', 'created_at')


class TokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    token_type = serializers.CharField(default='bearer')
    expires_in = serializers.IntegerField()
    user = UserSerializer()


# ==================== LOCATION SERIALIZERS ====================

class LocationAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationAddress
        fields = '__all__'


class LockerLocationListSerializer(serializers.ModelSerializer):
    address = LocationAddressSerializer(read_only=True)
    available_lockers = serializers.IntegerField(source='available_lockers_count', read_only=True)
    total_lockers = serializers.IntegerField(source='total_lockers_count', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    location_id = serializers.IntegerField(source='id', read_only=True)
    
    class Meta:
        model = LockerLocation
        fields = ('location_id', 'id', 'name', 'description', 'image', 'operating_hours_start',
                  'operating_hours_end', 'is_active', 'contact_phone', 'address',
                  'available_lockers', 'total_lockers', 'average_rating')


class LockerLocationDetailSerializer(LockerLocationListSerializer):
    """Detailed serializer with lockers"""
    pass


# ==================== PRICING SERIALIZERS ====================

class PricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingTier
        fields = '__all__'


# ==================== LOCKER SERIALIZERS ====================

class LockerUnitSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    locker_id = serializers.IntegerField(source='id', read_only=True)
    location_id = serializers.IntegerField(source='location.id', read_only=True)
    hourly_rate = serializers.DecimalField(source='tier.hourly_rate', 
                                            max_digits=10, decimal_places=2, read_only=True)
    daily_rate = serializers.DecimalField(source='tier.daily_rate',
                                           max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = LockerUnit
        fields = ('locker_id', 'id', 'location', 'location_id', 'location_name', 'unit_number', 'size', 
                  'status', 'hourly_rate', 'daily_rate')


class AvailableLockerSerializer(serializers.ModelSerializer):
    """Serializer for available lockers with pricing"""
    location_name = serializers.CharField(source='location.name', read_only=True)
    locker_id = serializers.IntegerField(source='id', read_only=True)
    location_id = serializers.IntegerField(source='location.id', read_only=True)
    city = serializers.CharField(source='location.address.city', read_only=True)
    hourly_rate = serializers.DecimalField(source='tier.hourly_rate',
                                            max_digits=10, decimal_places=2, read_only=True)
    daily_rate = serializers.DecimalField(source='tier.daily_rate',
                                           max_digits=10, decimal_places=2, read_only=True)
    weekly_rate = serializers.DecimalField(source='tier.weekly_rate',
                                            max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = LockerUnit
        fields = ('locker_id', 'id', 'location', 'location_id', 'location_name', 'city', 'unit_number', 
                  'size', 'status', 'hourly_rate', 'daily_rate', 'weekly_rate')


# ==================== DISCOUNT SERIALIZERS ====================

class DiscountSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Discount
        fields = ('id', 'code', 'description', 'discount_type', 'discount_value',
                  'min_booking_amount', 'max_discount_amount', 'valid_from', 
                  'valid_to', 'is_valid')


class ValidateDiscountSerializer(serializers.Serializer):
    code = serializers.CharField()
    booking_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


# ==================== BOOKING SERIALIZERS ====================

class CreateBookingSerializer(serializers.Serializer):
    locker_id = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    booking_type = serializers.ChoiceField(choices=Booking.BookingType.choices, default='Storage')
    discount_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")
        return data


class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    locker = LockerUnitSerializer(read_only=True)
    location_name = serializers.CharField(source='locker.location.name', read_only=True)
    booking_id = serializers.IntegerField(source='id', read_only=True)
    locker_id = serializers.IntegerField(source='locker.id', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    unit_number = serializers.CharField(source='locker.unit_number', read_only=True)
    size = serializers.CharField(source='locker.size', read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Booking
        fields = ('booking_id', 'id', 'user', 'user_id', 'locker', 'locker_id', 'location_name', 
                  'unit_number', 'size', 'start_time', 'end_time',
                  'duration_hours', 'booking_type', 'subtotal_amount', 'discount_amount',
                  'total_amount', 'status', 'created_at')


class BookingListSerializer(serializers.ModelSerializer):
    """Lighter serializer for lists"""
    location_name = serializers.CharField(source='locker.location.name', read_only=True)
    unit_number = serializers.CharField(source='locker.unit_number', read_only=True)
    size = serializers.CharField(source='locker.size', read_only=True)
    booking_id = serializers.IntegerField(source='id', read_only=True)
    locker_id = serializers.IntegerField(source='locker.id', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = Booking
        fields = ('booking_id', 'id', 'user_id', 'locker_id', 'location_name', 'unit_number', 'size', 'start_time', 
                  'end_time', 'total_amount', 'status', 'created_at')


class CancelBookingSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


# ==================== PAYMENT SERIALIZERS ====================

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ('id', 'method_type', 'card_last_four', 'card_holder_name',
                  'expiry_month', 'expiry_year', 'is_default', 'is_active')
        read_only_fields = ('id',)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'booking', 'amount', 'payment_date', 'transaction_reference',
                  'status', 'failure_reason')


# ==================== REVIEW SERIALIZERS ====================

class CreateReviewSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='booking.user.full_name', read_only=True)
    location_name = serializers.CharField(source='booking.locker.location.name', read_only=True)
    
    class Meta:
        model = Review
        fields = ('id', 'booking', 'user_name', 'location_name', 'rating', 
                  'title', 'comment', 'is_verified', 'created_at')


# ==================== QR CODE SERIALIZERS ====================

class QRCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRAccessCode
        fields = ('id', 'code', 'code_type', 'generated_at', 'expires_at', 'is_used')


class GenerateQRSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    code_type = serializers.ChoiceField(choices=QRAccessCode.CodeType.choices, default='Unlock')


# ==================== NOTIFICATION SERIALIZERS ====================

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'notification_type', 'related_booking',
                  'is_read', 'read_at', 'created_at')
