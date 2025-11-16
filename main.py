# main.py
# KivyMD client+driver app for "تاكسي مصر" — unified app (client + driver)
# Integrates with backend endpoints (FastAPI) when available, and falls back to simulation.


import os   # استيراد مكتبة os للتعامل مع ملفات النظام (زي التحقق من وجود ملف أو تحديد مسار)
import threading  # استيراد مكتبة threading لتشغيل مهام في الخلفية (زي إرسال الموقع أو استقبال WebSocket)
import time   # استيراد مكتبة time للتحكم في التأخيرات (sleep) أو حساب الزمن
import random  # استيراد مكتبة random لتوليد أرقام عشوائية (تستخدم في المحاكاة)
import json  # استيراد مكتبة json للتعامل مع البيانات بصيغة JSON (تحويل dict <-> نص JSON)
import math # استيراد مكتبة math وهي مكتبة مدمجة في بايثون تحتوي على دوال رياضية جاهزة# مثل sin(), cos(), sqrt(), pow() وغيرها من العمليات الرياضية المفيدة# تُستخدم مثلاً لحساب المسافات بين نقطتين على الخريطة أو لتحويل الزوايا
from openai import OpenAI # استيراد مكتبة openai للتعامل مع واجهة برمجة تطبيقات OpenAI API# تُستخدم هنا غالباً لتشغيل الشات بوت أو الذكاء الاصطناعي داخل التطبيق# مثل توقع سعر الرحلة أو الرد على استفسارات المستخدمين
from typing import Optional # استيراد النوع Optional من مكتبة typing (المخصصة لتوضيح أنواع البيانات)
                             # يُستخدم في التوصيفات (type hints) لتحديد أن المتغير أو الدالة قد تكون None أو نوع معين # مثال: def func(x: Optional[int]) يعني أن x يمكن أن تكون رقمًا أو None
import requests  # استيراد مكتبة requests لإرسال واستقبال طلبات HTTP من السيرفر
from websocket import create_connection, WebSocketConnectionClosedException   # لإنشاء اتصال WebSocket مع السيرفر

from kivy.lang import Builder   # لتحميل أكواد التصميم المكتوبة بلغة KV الخاصة بـ Kivy
from kivy.core.window import Window  # للتحكم في خصائص نافذة التطبيق (زي الحجم)
from kivy.uix.screenmanager import ScreenManager, Screen # لإدارة التنقل بين الشاشات (ScreenManager)
from kivy.clock import Clock  # تستخدم لتشغيل أكواد على Thread الواجهة أو بعد تأخير معين
from kivy_garden.mapview import MapView, MapMarker   # مكون خريطة تفاعلية MapView لإظهار المواقع والعلامات
from kivymd.app import MDApp  # فئة التطبيق الأساسية من مكتبة KivyMD (واجهة الماتيريال ديزاين)
from kivymd.uix.dialog import MDDialog   # نافذة حوار من KivyMD (تُستخدم لتنبيهات المستخدم)
from kivymd.uix.button import MDFlatButton, MDRaisedButton  # أزرار مسطحة وبارزة من KivyMD
from kivy.core.text import LabelBase   # لتسجيل خطوط (Fonts) مخصصة في Kivy
from kivy.metrics import dp  # استيراد دالة dp من مكتبة kivy.metrics لتحويل القيم إلى "density-independent pixels"# تستخدم لتحديد المسافات أو الأحجام بحيث تكون مناسبة لجميع الشاشات (تتغير حسب دقة الشاشة)
from kivy.uix.boxlayout import BoxLayout  # استيراد عنصر BoxLayout وهو نوع من الـ Layout في كـيفي لترتيب العناصر  # يستخدم لترتيب الأدوات (widgets) بشكل أفقي أو عمودي داخل الواجهة
from kivymd.uix.screen import MDScreen # استيراد MDScreen من مكتبة KivyMD، وهي شاشة (صفحة) ضمن واجهة التطبيق# تُستخدم لعرض واجهة معينة مثل شاشة تسجيل الدخول أو صفحة الخريطة
from kivymd.uix.list import OneLineListItem  # استيراد OneLineListItem من KivyMD لإنشاء عنصر قائمة يحتوي على سطر واحد فقط من النص  # يُستخدم غالباً في القوائم (مثل عرض أسماء المدن أو السائقين)
from kivy.clock import mainthread # استيراد mainthread من kivy.clock لتشغيل دوال معينة داخل الـ "thread" الرئيسي للواجهة # هذا مهم لأن واجهة كـيفي لا تسمح بتحديث العناصر من Thread خارجي، لذلك نستخدم @mainthread # لتحديث الواجهة بأمان بعد عمليات مثل استقبال بيانات من الإنترنت أو WebSocket
from kivy.clock import Clock
from kivy.uix.image import Image  # استيراد Image بدلاً من Video للخلفية الثابتة

# register Arabic Cairo font if exists (optional)
if os.path.exists("Cairo-Regular.ttf"):
    LabelBase.register(name="Arabic", fn_regular="Cairo-Regular.ttf")    # التحقق من وجود خط Cairo-Regular.ttf في المجلد الحالي

# optional window size for desktop testing
Window.size = (400, 700) # تحديد حجم نافذة التطبيق في وضع الاختبار (على الكمبيوتر)

import openai
# ================== إعداد OpenAI ==================
OPENAI_API_KEY = "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"  # ضع مفتاحك هنا
openai.api_key = OPENAI_API_KEY

# ================== أسئلة مبرمجة مسبقًا ==================
PREDEFINED_QA = {
    "What is the price of a taxi?": "The taxi fare varies depending on the distance, usually 10 pounds per kilometer.",
    "How do I book a taxi?": "You can book through the app or by calling the hotline.",
    "Is there a discount for long-distance flights?": "Yes, there are discounts on long-haul flights according to current offers.",
    "What is the payment method?": "You can pay in cash or by credit card within the app.",
    "trip cairo to giza?": "360pounds & 40km"
}

# ================== أسئلة مقترحة تظهر بجانب مربع الكتابة ==================
QUICK_QUESTIONS = [
"What is the price of a taxi?",
"How do I book a taxi?",
"Is there a discount for long trips?",
"What are the payment methods?",
"trip cairo to giza?"
]



KV = """          
ScreenManager:
    SplashScreen:
    RoleScreen:
    LoginScreen:
    TermsScreen:
    WelcomeScreen:
    ClientHomeScreen:
    ClientMapPickScreen:
    ClientTrackingScreen:
    DriverHomeScreen:
    DriverTripsScreen:
    DriverTrackingScreen:
    PaymentScreen:
    ChatScreen:

# ==========================
# شاشة البداية (Splash)
# ==========================
<SplashScreen>:
    name: "splash"
    MDFloatLayout:
        Image:
            source: "car_background.jpeg"
            allow_stretch: True
            keep_ratio: False
            opacity: 0.5

        MDLabel:
            text: "EGTaxi"
            halign: "center"
            font_style: "H3"
            pos_hint: {"center_y": 0.55}

        MDRaisedButton:
            text: "Start"
            md_bg_color: app.theme_cls.primary_color
            size_hint: .6, None
            height: dp(48)
            pos_hint: {"center_x": 0.5, "y": 0.08}
            on_release: app.open_role()

# ==========================
# اختيار الدور (عميل / سائق)
# ==========================
<RoleScreen>:
    name: "role"
    MDFloatLayout:
        Image:
            source: "car_background.jpeg"
            allow_stretch: True
            keep_ratio: False
            opacity: 0.5

        MDTopAppBar:
            title: "Choose Role"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["theme-light-dark", lambda x: app.toggle_theme()]] 

        MDLabel:
            text: "Select your role"
            halign: "center"
            font_style: "H5"
            pos_hint: {"center_y": 0.75}

        MDRaisedButton:
            text: "Client"
            size_hint: .4, None
            height: dp(48)
            pos_hint: {"center_x": 0.3, "y": 0.45}
            on_release: app.set_role("client")

        MDRaisedButton:
            text: "Driver"
            size_hint: .4, None
            height: dp(48)
            pos_hint: {"center_x": 0.7, "y": 0.45}
            on_release: app.set_role("driver")

# ==========================
# تسجيل الدخول / OTP
# ==========================
<LoginScreen>:
    name: "login"
    MDFloatLayout:
        Image:
            source: "car_background.jpeg"
            allow_stretch: True
            keep_ratio: False
            opacity: 0.5

        MDTopAppBar:
            title: "Login / Register"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["theme-light-dark", lambda x: app.toggle_theme()]]

        MDTextField:
            id: phone
            hint_text: "Enter phone number (01012345678)"
            pos_hint: {"center_x": 0.5, "center_y": 0.65}
            size_hint_x: 0.85
            max_text_length: 11
            input_filter: "int"

        MDRaisedButton:
            text: "Send Verification Code"
            size_hint: .6, None
            height: dp(44)
            pos_hint: {"center_x": 0.5, "y": 0.48}
            on_release: app.send_otp(phone.text)

        MDTextField:
            id: otp_code
            hint_text: "Enter verification code"
            pos_hint: {"center_x": 0.5, "center_y": 0.42}
            size_hint_x: 0.6

        MDRaisedButton:
            text: "Verify & Continue"
            size_hint: .6, None
            height: dp(44)
            pos_hint: {"center_x": 0.5, "y": 0.28}
            on_release: app.verify_otp(phone.text, otp_code.text)

# ==========================
# شاشة الشروط
# ==========================
<TermsScreen>:
    name: "terms"
    MDFloatLayout:
        Image:
            source: "car_background.jpeg"
            allow_stretch: True
            keep_ratio: False
            opacity: 0.5

        MDTopAppBar:
            title: "Terms"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]


        MDLabel:
            text: "I confirm I am over 18 years old."
            halign: "center"
            pos_hint: {"center_y": 0.6}

        MDRaisedButton:
            text: "Agree"
            pos_hint: {"center_x": 0.5, "y": 0.4}
            on_release: app.accept_terms()

# ==========================
# شاشة الترحيب
# ==========================
<WelcomeScreen>:
    name: "welcome"
    MDFloatLayout:
        Image:
            source: "car_background.jpeg"
            allow_stretch: True
            keep_ratio: False
            opacity: 0.5

        MDTopAppBar:
            title: "Welcome"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["theme-light-dark", lambda x: app.toggle_theme()]]

        MDLabel:
            text: "Welcome to EGTAXI"
            halign: "center"
            pos_hint: {"center_y": 0.6}

        MDRaisedButton:
            text: "Start"
            pos_hint: {"center_x": 0.5, "y": 0.18}
            size_hint: .6, None
            height: dp(44)
            on_release: app.open_home()

# ==========================
# واجهة العميل الرئيسية
# ==========================
<ClientHomeScreen>:
    name: "client_home"
    MDFloatLayout:
        Image:
            source: "car_background.jpeg"
            allow_stretch: True
            keep_ratio: False
            opacity: 0.5

        MDTopAppBar:
            title: "Home"
            pos_hint: {"top": 1}
            elevation: 10
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["theme-light-dark", lambda x: app.toggle_theme()]]

        ScrollView:
            size_hint_y: 0.85
            pos_hint: {"top": 0.9}
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(8)
                padding: dp(8)
                adaptive_height: True

                MDCard:
                    size_hint_y: None
                    height: dp(100)
                    padding: dp(8)
                    MDBoxLayout:
                        orientation: "vertical"
                        MDLabel:
                            text: "Pick-up location"
                            halign: "left"
                        MDBoxLayout:
                            orientation: "horizontal"
                            spacing: dp(8)
                            MDTextField:
                                id: from_text
                                hint_text: "From (address or tap map)"
                                size_hint_x: 0.7
                            MDRaisedButton:
                                text: "Map"
                                on_release: app.open_map_pick("from")

                MDCard:
                    size_hint_y: None
                    height: dp(100)
                    padding: dp(8)
                    MDBoxLayout:
                        orientation: "vertical"
                        MDLabel:
                            text: "Drop-off location"
                            halign: "left"
                        MDBoxLayout:
                            orientation: "horizontal"
                            spacing: dp(8)
                            MDTextField:
                                id: to_text
                                hint_text: "To (address or tap map)"
                                size_hint_x: 0.7
                            MDRaisedButton:
                                text: "Map"
                                on_release: app.open_map_pick("to")

                MDCard:
                    size_hint_y: None
                    height: dp(80)
                    padding: dp(8)
                    MDBoxLayout:
                        orientation: "horizontal"
                        spacing: dp(8)
                        MDLabel:
                            text: "Trip type:"
                            size_hint_x: 0.3
                            halign: "right"
                        MDRectangleFlatButton:
                            text: "Normal"
                            on_release: app.set_trip_type("normal")
                        MDRectangleFlatButton:
                            text: "Special Needs"
                            on_release: app.set_trip_type("special")
                MDCard:
                    size_hint_y: None
                    height: dp(78)
                    padding: dp(8)
                    MDBoxLayout:
                        orientation: "horizontal"
                        spacing: dp(8)
                        MDLabel:
                            text: "Type of car:"
                            
                            size_hint_x: 0.35
                            halign: "right"
                        MDSwitch:
                            id: car_switch
                            size_hint_x: 0.15
                            on_active: app.on_car_type(self.active)
                        MDLabel:
                            id: car_type_label
                            text: "Old / Modern"
                            
                            halign: "left"
                        MDLabel:
                            text: "Price system:"
                            
                            halign: "right"
                            size_hint_x: 0.3
                        MDSpinner:
                            id: price_mode_dummy
                            size_hint: None, None
                            size: dp(10), dp(10)
                            active: False
                        MDIconButton:
                            id: meter_btn
                            icon: "counter"
                            on_release: app.set_price_mode("meter")
                        MDIconButton:
                            id: fixed_btn
                            icon: "currency-usd"
                            on_release: app.set_price_mode("fixed")
                MDBoxLayout:
                    size_hint_y: None
                    height: dp(64)
                    padding: dp(8)
                    spacing: dp(8)
                    MDRaisedButton:
                        text: "Show Drivers"
                        on_release: app.show_available_drivers()
                    MDRaisedButton:
                        text: "Voice Request"
                        on_release: app.voice_request()
                    MDRaisedButton:
                        text: "💬 Chatbot"
                        on_release: app.root.current = "chat"

# ==========================
# شاشة الخريطة (بدون خلفية)
# ==========================
<ClientMapPickScreen>:
    name: "map_pick"
    BoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Select on Map"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["check", lambda x: app.confirm_map_pick()]]

        MapView:
            id: pick_map
            lat: 30.0444
            lon: 31.2357
            zoom: 12

# ==========================
# تتبع العميل (بدون خلفية)
# ==========================
<ClientTrackingScreen>:
    name: "client_tracking"
    BoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Driver Tracking"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["alert-circle", lambda x: app.sos_dialog()]]

        MapView:
            id: tracking_map
            lat: 30.0444
            lon: 31.2357
            zoom: 13
        MDBoxLayout:
            size_hint_y: None
            height: dp(64)
            padding: dp(8)
            spacing: dp(8)
            MDLabel:
                id: eta_label
                text: "ETA: --"
                halign: "center"
            MDRaisedButton:
                text: "Cancel Trip"
                on_release: app.cancel_trip()

# ==========================
# باقي الشاشات (Driver + Payment + Chat)
# ==========================
<DriverHomeScreen>:
    name: "driver_home"
    MDFloatLayout:
        Image:
            source: "car_background.jpeg"
            allow_stretch: True
            keep_ratio: False
            opacity: 0.5

        MDTopAppBar:
            title: "Driver Dashboard"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["map-marker-path", lambda x: app.open_driver_trips()], ["theme-light-dark", lambda x: app.toggle_theme()]]

        BoxLayout:
            pos_hint: {"top": 0.90}
            orientation: "vertical"
            padding: dp(8)
            spacing: dp(8)
            MDTextField:
                id: car_model
                hint_text: "Car model (e.g., 2015)"
            MDRaisedButton:
                id: start_receive_btn
                text: "Start receiving trips"
                on_release: app.start_driver()
            MDLabel:
                id: driver_status
                text: "Accepted trips: 0"
                halign: "center"

<DriverTripsScreen>:
    name: "driver_trips"
    BoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Available Trips"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            elevation: 6
            
        ScrollView:
            MDList:
                id: pending_list

<DriverTrackingScreen>:
    name: "driver_tracking"
    BoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Journey"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["alert-circle", lambda x: app.sos_dialog()]]

        MapView:
            id: driver_map
            lat: 30.0444
            lon: 31.2357
            zoom: 13
        MDBoxLayout:
            size_hint_y: None
            height: dp(64)
            padding: dp(8)
            spacing: dp(8)
            MDRaisedButton:
                id: driver_start_btn
                text: "Start Trip"
                on_release: app.driver_start_ride()
            MDRaisedButton:
                id: driver_end_btn
                text: "Stop Trip"
                on_release: app.driver_end_ride()

<PaymentScreen>:
    name: "payment"
    MDFloatLayout:
        Image:
            source: "car_background.jpeg"
            allow_stretch: True
            keep_ratio: False
            opacity: 0.4

        MDTopAppBar:
            title: "Payment"
            pos_hint: {"top": 1}
            left_action_items: [["arrow-left", lambda x: app.go_back()]]


        BoxLayout:
            orientation: "vertical"
            padding: dp(12)
            spacing: dp(8)
            MDLabel:
                id: final_price
                text: "Price: --"
            MDRaisedButton:
                text: "Pay by Card"
                on_release: app.pay("card")
            MDRaisedButton:
                text: "Cash Payment"
                on_release: app.pay("cash")

<ChatScreen>:
    name: "chat"
    MDFloatLayout:
        
        MDBoxLayout:
            orientation: "vertical"
            MDTopAppBar:
                title: "Smart Assistant"
                pos_hint: {"top": 1}
                left_action_items: [["arrow-left", lambda x: app.go_back()]]
            

            ScrollView:
                MDList:
                    id: chat_list

        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            spacing: "5dp"

            MDGridLayout:
                cols: 2
                size_hint_y: None
                height: self.minimum_height
                id: quick_buttons

            MDTextField:
                id: user_input
                hint_text: "Write your inquiry here"
                on_text_validate: app.send_message()
            MDRaisedButton:
                text: "send"
                on_release: app.send_message()



"""

# Screens classes (empty — logic lives in MDApp)
class SplashScreen(Screen): pass
class RoleScreen(Screen): pass
class LoginScreen(Screen): pass
class TermsScreen(Screen): pass
class WelcomeScreen(Screen): pass
class ClientHomeScreen(Screen): pass
class ClientMapPickScreen(Screen): pass
class ClientTrackingScreen(Screen): pass
class DriverHomeScreen(Screen): pass
class DriverTripsScreen(Screen): pass
class DriverTrackingScreen(Screen): pass
class PaymentScreen(Screen): pass
class ChatScreen(MDScreen): pass

# ------------------- Helper functions -------------------
def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers between two lat/lon points."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ------------------- Main App -------------------
class TaxiApp(MDApp):
    # app state
    role: Optional[str] = None  # "client" or "driver"
    user: Optional[dict] = None
    dialog: Optional[MDDialog] = None

    # map / trip state
    map_pick_state: Optional[str] = None
    picked_location: Optional[tuple] = None
    price_mode: str = "meter"  # "meter" or "fixed"

    # markers
    map_markers = {}
    client_marker = None
    driver_marker = None

    # current trip
    current_trip: Optional[dict] = None

    # websockets
    client_ws = None
    driver_ws = None

    # driver simulator thread control
    _driver_location_thread = None
    _driver_location_thread_stop = threading.Event()

    # إعداد عنوان السيرفر الخلفي (backend API) والـ WebSocket
    BACKEND = "http://127.0.0.1:8000"  # السيرفر المحلي (backend API)
    WS_BASE = "ws://127.0.0.1:8000"  # عنوان WebSocket المحلي (يُستخدم للتحديث المباشر)
# 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
    def build(self):
        self.title = "Taxi ChatBot"
        self.theme_cls.theme_style = "Dark"  # خلفية داكنة
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "500"
        self.lang = "en"
        self.previous_screen = None
        self.generated_otp = None
        self.trip_type = "normal"
        self.role = None
        self.history = []  # تاريخ الشاشات

        # إنشاء ScreenManager من KV
        self.sm = Builder.load_string(KV)
        return self.sm  # مهم: ترجع widget واحد فقط

        

    # ------------------- Helper functions -------------------
    def haversine_km(lat1, lon1, lat2, lon2):
        """Calculate distance in kilometers between two lat/lon points."""
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    # ---------- Navigation ----------
    def push(self, name):
        """إضافة شاشة للتاريخ"""
        if self.root.current != name:
            self.history.append(self.root.current)
            self.root.current = name

    def pop(self):
        """الرجوع إلى الشاشة السابقة"""
        if self.history:
            last = self.history.pop()
            self.root.current = last
        else:
            self.root.current = "splash"  # إذا لم يكن هناك تاريخ، رجوع إلى البداية

    def go_back(self):
        self.pop()

    def open_role(self):
        self.push("role")

    def set_role(self, role):
        self.role = role
        self.push("login")

    def accept_terms(self):
        self.push("welcome")

    def open_home(self):
        if self.role == "client":
            self.push("client_home")
        else:
            self.push("driver_home")

    # ---------------------------
    # 🌞 / 🌙 Theme Toggle
    # ---------------------------
    def toggle_theme(self):
        """Switch between light and dark modes."""
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.theme_style = "Light"
        else:
            self.theme_cls.theme_style = "Dark"
    
    
    # ---------------------------
    # 🔐 Phone Verification
    # ---------------------------
    def send_otp(self, phone_number):
        """Send OTP using backend or simulation."""
        if len(phone_number) != 11:
            self.show_dialog("Error", "Please enter a valid phone number (11 digits).")
            return

        try:
            res = requests.post(f"{self.BACKEND}/send-otp", json={"phone": phone_number}, timeout=6)
            if res.status_code == 200:
                self.show_dialog("Verification", "OTP sent successfully.")
            else:
                self.show_dialog("Error", "Failed to send OTP.")
        except Exception:
            # Simulation fallback
            self.generated_otp = str(random.randint(1000, 9999))
            print(f"OTP sent to {phone_number}: {self.generated_otp}")
            self.show_dialog("Verification", "A verification code was sent to your phone (simulated).")

    def verify_otp(self, phone_number, entered_code):
        """Verify OTP using backend or simulation."""
        try:
            res = requests.post(f"{self.BACKEND}/verify-otp", json={"phone": phone_number, "code": entered_code}, timeout=6)
            if res.status_code == 200:
                self.show_dialog("Success", "Phone verified successfully.")
                Clock.schedule_once(lambda dt: self.push("terms"), 1)
            else:
                self.show_dialog("Error", "Invalid verification code.")
        except Exception:
            # Simulation fallback
            if not self.generated_otp:
                self.show_dialog("Error", "Please request a verification code first.")
                return
            if entered_code == self.generated_otp:
                self.show_dialog("Success", "Phone number verified successfully.")
                Clock.schedule_once(lambda dt: self.push("terms"), 1)
            else:
                self.show_dialog("Error", "Incorrect verification code.")


    
    # ---------------------------
    # 🚗 Trip Type
    # ---------------------------
    def set_trip_type(self, trip_type):
        self.trip_type = trip_type
        if trip_type == "special":
            self.show_dialog("Trip Type", "Special needs trip selected.")
        else:
            self.show_dialog("Trip Type", "Normal trip selected.")
    
    
    # ---------------------------
    # 💬 Chatbot Placeholder
    # ---------------------------
    def on_start(self):
        # self.root موجود الآن
        self.add_quick_buttons()
    def add_quick_buttons(self):
        chat_screen = self.root.get_screen("chat")  # تصحيح هنا
        for q in QUICK_QUESTIONS:
            btn = OneLineListItem(text=q, on_release=lambda x, msg=q: self.send_quick_message(msg))
            chat_screen.ids.quick_buttons.add_widget(btn)

    def send_quick_message(self, msg):
        chat_screen = self.root.get_screen("chat")  # تصحيح هنا
        chat_screen.ids.user_input.text = msg
        self.send_message()

    def send_message(self):
        chat_screen = self.root.get_screen("chat")  # تصحيح هنا
        user_input = chat_screen.ids.user_input.text.strip()
        chat_list = chat_screen.ids.chat_list

        if not user_input:
            return

        chat_list.add_widget(OneLineListItem(text=f"you: {user_input}"))
        chat_screen.ids.user_input.text = ""

        # تشغيل الرد في Thread لتجنب تجميد الواجهة
        threading.Thread(target=self.get_bot_reply, args=(user_input,)).start()
     # ======= دوال البوت =======
    def get_bot_reply(self, message):
        try:
            if any(word in message.lower() for word in ["taxi","price","booking","trip","payment","discount"]):
                reply = self.query_openai(message)
            else:
                reply = self.get_predefined_reply(message)
        except Exception as e:
            print("🔴 Error:", e)
            reply = self.get_predefined_reply(message)
        self.show_bot_reply(reply)

    def query_openai(self, message):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}],
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print("⚠️ OpenAI error:", e)
            return self.get_predefined_reply(message)

    def get_predefined_reply(self, message):
        for key in PREDEFINED_QA:
            if key in message:
                return PREDEFINED_QA[key]
        return "Sorry, I don't understand your question. You can choose one of the frequently asked questions."

    
    @mainthread
    def show_bot_reply(self, text):
        chat_screen = self.root.get_screen("chat")  # تصحيح هنا
        chat_screen.ids.chat_list.add_widget(
            OneLineListItem(text=f"intelligence: {text}")
        )

    
    # ---------------------------
    # 🧩 Helper Functions
    # ---------------------------
    def show_dialog(self, title, text):
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[MDRaisedButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
        )
        self.dialog.open()
    # ---------- Auth ----------
    def login(self, phone: str):
        if not phone or not str(phone).strip():
            self._notify("Please enter the phone number")
            return
        phone = str(phone).strip()
        self._notify("Contacting server...")
        try:
            r = requests.post(f"{self.BACKEND}/login", json={"phone": phone}, timeout=6)
            data = r.json()
            if data.get("status") == "success":
                self.user = data
                if "user_id" not in self.user and "id" in self.user:
                    self.user["user_id"] = self.user["id"]
                self._notify("Login successful")
                self.push("terms")
            else:
                self._notify(data.get("message") or "Login failed")
        except Exception as e:
            # fallback: simulate creating a user locally
            self.user = {"user_id": random.randint(1000, 9999), "name": "مستخدم جديد", "role": self.role or "client", "phone": phone}
            self._notify(f"Backend not reachable — simulated login as {self.user['user_id']}")
            self.push("terms")

    def show_dialog(self, title: str, text: str):
        """إظهار نافذة حوار بسيطة"""
        if self.dialog:
            try:
                self.dialog.dismiss()
            except:
                pass
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="موافق" if self.lang == "ar" else "OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

    # ---------- Map pick ----------
    def open_map_pick(self, field: str):
        self.map_pick_state = field
        self.root.current = "map_pick"
        Clock.schedule_once(self._bind_pick_map, 0.2)

    def _bind_pick_map(self, dt):
        try:
            m = self.root.get_screen("map_pick").ids.pick_map
            try:
                m.unbind(on_touch_down=self._on_map_touch)
            except Exception:
                pass
            m.bind(on_touch_down=self._on_map_touch)
        except Exception:
            pass

    def _on_map_touch(self, mapview: MapView, touch):
        if not mapview.collide_point(*touch.pos):
            return False
        try:
            lat, lon = mapview.get_latlon_at(touch.x, touch.y)
        except Exception:
            try:
                lat, lon = mapview.get_latlon_at(touch.pos[0], touch.pos[1])
            except Exception:
                return False
        self.picked_location = (lat, lon)
        self._notify(f"The location has been determined: {lat:.5f}, {lon:.5f}")
        try:
            key = f"pick_{self.map_pick_state}"
            screen = self.root.get_screen("map_pick")
            # remove earlier pick markers
            for k, child in list(self.map_markers.items()):
                if k.startswith("pick_"):
                    try:
                        screen.ids.pick_map.remove_widget(child)
                    except Exception:
                        pass
                    del self.map_markers[k]
            # add new marker
            marker = MapMarker(lat=lat, lon=lon)
            self.map_markers[key] = marker
            screen.ids.pick_map.add_widget(marker)
        except Exception:
            pass
        return True

    def confirm_map_pick(self):
        if not self.picked_location:
            self._notify("You haven't chosen a location yet")
            return
        lat, lon = self.picked_location
        if self.map_pick_state == "from":
            self.root.get_screen("client_home").ids.from_text.text = f"{lat:.5f},{lon:.5f}"
        else:
            self.root.get_screen("client_home").ids.to_text.text = f"{lat:.5f},{lon:.5f}"
        self.picked_location = None
        # remove pick markers
        try:
            screen = self.root.get_screen("map_pick")
            for k, m in list(self.map_markers.items()):
                if k.startswith("pick_"):
                    try:
                        screen.ids.pick_map.remove_widget(m)
                    except Exception:
                        pass
                    del self.map_markers[k]
        except Exception:
            pass
        self.root.current = "client_home"

    def close_map_pick(self):
        self.picked_location = None
        self.root.current = "client_home"

    # ---------- Client flow ----------
    def on_car_type(self, active: bool):
        lbl = self.root.get_screen("client_home").ids.car_type_label
        lbl.text = "New" if active else "Old"

    def set_price_mode(self, mode: str):
        self.price_mode = mode
        try:
            btn = self.root.get_screen("client_home").ids.start_trip_btn
            btn.opacity = 1
            btn.disabled = False
        except Exception:
            pass
        self._notify(f"The price option selected: {'Electronic meter' if mode=='meter' else 'Fixed price'}")

    def show_available_drivers(self):
        self.start_trip(simulate_only=False)

    def start_trip(self, simulate_only: bool = False):
        """Client starts trip request: tries to call backend /available_drivers
           If backend unreachable, falls back to simulated drivers.
           If user selects a driver, create trip via /trips or simulate.
        """
        from_val = self.root.get_screen("client_home").ids.from_text.text
        to_val = self.root.get_screen("client_home").ids.to_text.text
        if not from_val or not to_val:
            self._notify("Choose your starting point and destination first.")
            return

        self._notify("Searching for available drivers...")
        drivers = []
        if not simulate_only:
            try:
                payload = {"from": from_val, "to": to_val, "price_mode": self.price_mode}
                r = requests.post(f"{self.BACKEND}/available_drivers", json=payload, timeout=6)
                data = r.json()
                drivers = data.get("drivers", [])
            except Exception as e:
                # backend might not have /available_drivers — fall through to simulation
                print("available_drivers error:", e)

        if not drivers:
            # simulate drivers near pickup
            try:
                # parse coordinates if provided
                if "," in from_val:
                    lat0 = float(from_val.split(",")[0])
                    lon0 = float(from_val.split(",")[1])
                else:
                    lat0, lon0 = 30.0444, 31.2357
            except Exception:
                lat0, lon0 = 30.0444, 31.2357

            drivers = [
                {"id": 101, "name": "Mahmoud", "car": "Toyota 2018", "type": "new", "price": 85,
                 "lat": lat0 + 0.004, "lng": lon0 - 0.004},
                {"id": 102, "name": "Ahmed", "car": "Hyundai 2009", "type": "old", "price": 70,
                 "lat": lat0 - 0.0035, "lng": lon0 + 0.0035},
                {"id": 103, "name": "Sami", "car": "Nissan 2016", "type": "new", "price": 95,
                 "lat": lat0 + 0.006, "lng": lon0 + 0.002},
            ]

        # create dialog with drivers
        buttons = []
        for d in drivers:
            # show estimated distance to client if coordinates exist
            dist_text = ""
            try:
                if "lat" in d and "lng" in d:
                    if "," in from_val:
                        fl = float(from_val.split(",")[0]); fn = float(from_val.split(",")[1])
                        km = haversine_km(fl, fn, d["lat"], d["lng"])
                        dist_text = f" | {km:.1f} km away"
            except Exception:
                dist_text = ""
            text = f"{d['name']} | {d.get('car','-')} | {d.get('type','-')} | {d.get('price','-')} ج{dist_text}"
            def make_cb(driver):
                return lambda *a: self._select_driver_and_book(driver)
            buttons.append(MDRaisedButton(text=text, on_release=make_cb(d)))

        content = BoxLayout(orientation="vertical", spacing=dp(8))
        for b in buttons:
            content.add_widget(b)
        dlg = MDDialog(title="Available drivers", type="custom", content_cls=content,
                       size_hint=(0.9, 0.7),
                       buttons=[MDFlatButton(text="close", on_release=lambda x: dlg.dismiss())])
        dlg.open()

    def _select_driver_and_book(self, driver: dict):
        # Called when client selects a driver from dialog
        # Prepare trip payload
        from_text = self.root.get_screen("client_home").ids.from_text.text
        to_text = self.root.get_screen("client_home").ids.to_text.text
        def parse_coord(txt, default_lat, default_lng):
            try:
                if "," in txt:
                    a, b = txt.split(",")
                    return float(a), float(b)
            except Exception:
                pass
            return default_lat, default_lng

        f_lat, f_lng = parse_coord(from_text, 30.0444, 31.2357)
        t_lat, t_lng = parse_coord(to_text, 30.0500, 31.2400)

        payload = {
            "client_id": self.user.get("user_id") if self.user else None,
            "driver_id": driver.get("id"),
            "from_lat": f_lat, "from_lng": f_lng,
            "to_lat": t_lat, "to_lng": t_lng,
            "price": driver.get("price", 0),
            "status": "pending"
        }

        # try to create trip on backend
        trip = None
        try:
            r = requests.post(f"{self.BACKEND}/trips", json=payload, timeout=6)
            data = r.json()
            if data.get("status") == "success":
                trip_id = data.get("trip_id")
                payload["trip_id"] = trip_id
                trip = payload
                self._notify(f"Trip booked (id {trip_id})")
            else:
                # backend returned error, simulate
                trip = {**payload, "trip_id": random.randint(2000, 9999)}
                self._notify("Backend did not create trip; using simulated booking.")
        except Exception as e:
            trip = {**payload, "trip_id": random.randint(2000, 9999)}
            self._notify(f"Unable to reach backend: {e}\nSimulated trip #{trip['trip_id']}")

        # save current trip and open tracking
        self.current_trip = trip
        Clock.schedule_once(lambda dt: self._open_client_tracking_and_start_ws(trip), 0.3)

    def _open_client_tracking_and_start_ws(self, trip: dict):
        try:
            screen = self.root.get_screen("client_tracking")
            screen.ids.tracking_map.center_on(trip["from_lat"], trip["from_lng"])
            # client marker
            if self.client_marker:
                try: screen.ids.tracking_map.remove_widget(self.client_marker)
                except Exception: pass
            self.client_marker = MapMarker(lat=trip["from_lat"], lon=trip["from_lng"])
            screen.ids.tracking_map.add_widget(self.client_marker)
            # driver marker initial (if provided)
            if self.driver_marker:
                try: screen.ids.tracking_map.remove_widget(self.driver_marker)
                except Exception: pass
            # place driver a bit offset if no coords
            dlat = trip.get("driver_lat", trip["from_lat"] + 0.005)
            dlng = trip.get("driver_lng", trip["from_lng"] - 0.005)
            self.driver_marker = MapMarker(lat=dlat, lon=dlng)
            screen.ids.tracking_map.add_widget(self.driver_marker)
            self.root.current = "client_tracking"

            # start client websocket thread: subscribe to trip updates (server route: /ws/client/{trip_id})
            threading.Thread(target=self._client_ws_thread, args=(trip["trip_id"],), daemon=True).start()
        except Exception as e:
            print("open tracking error:", e)

    def _client_ws_thread(self, trip_id):
        ws_url = f"{self.WS_BASE}/ws/client/{trip_id}"
        try:
            ws = create_connection(ws_url, timeout=6)
            self.client_ws = ws
        except Exception as e:
            # fallback: simulate driver movement
            print("Client WS connect error (simulated):", e)
            for i in range(12):
                if not self.current_trip:
                    break
                try:
                    # move driver marker closer to client step by step
                    if self.driver_marker and self.client_marker:
                        lat = self.driver_marker.lat + (self.client_marker.lat - self.driver_marker.lat) * 0.18
                        lon = self.driver_marker.lon + (self.client_marker.lon - self.driver_marker.lon) * 0.18
                    else:
                        lat = self.current_trip["from_lat"] + 0.01 - i * 0.0008
                        lon = self.current_trip["from_lng"] - 0.01 + i * 0.0008
                    Clock.schedule_once(lambda dt, a=lat, b=lon: self._update_driver_marker(a, b))
                    eta = max(1, 10 - i)
                    Clock.schedule_once(lambda dt, s=eta: self._set_eta(s))
                    time.sleep(2)
                except Exception:
                    break
            return

        try:
            while True:
                try:
                    msg = ws.recv()
                except WebSocketConnectionClosedException:
                    break
                if not msg:
                    continue
                try:
                    data = json.loads(msg)
                except Exception:
                    continue
                # expect messages like {"event":"driver_location_update","driver_id":..,"lat":..,"lng":..,"eta":..}
                if data.get("event") == "driver_location_update":
                    lat = data.get("lat"); lon = data.get("lng"); eta = data.get("eta")
                    if lat is not None and lon is not None:
                        Clock.schedule_once(lambda dt, a=lat, b=lon: self._update_driver_marker(a, b))
                    if eta is not None:
                        Clock.schedule_once(lambda dt, s=eta: self._set_eta(s))
        finally:
            try:
                ws.close()
            except Exception:
                pass

    def _update_driver_marker(self, lat, lon):
        try:
            screen = self.root.get_screen("client_tracking")
            if not self.driver_marker:
                self.driver_marker = MapMarker(lat=lat, lon=lon)
                screen.ids.tracking_map.add_widget(self.driver_marker)
            else:
                try:
                    screen.ids.tracking_map.remove_widget(self.driver_marker)
                except Exception:
                    pass
                self.driver_marker = MapMarker(lat=lat, lon=lon)
                screen.ids.tracking_map.add_widget(self.driver_marker)
            screen.ids.tracking_map.center_on(lat, lon)
        except Exception as e:
            print("update driver marker err", e)

    def _set_eta(self, seconds):
        try:
            lbl = self.root.get_screen("client_tracking").ids.eta_label
            lbl.text = f"ETA: {seconds} min"
        except Exception:
            pass

    def cancel_trip(self):
        if not self.current_trip:
            self._notify("No active trip to cancel")
            return
        # request backend cancel (optional)
        try:
            requests.post(f"{self.BACKEND}/trips/{self.current_trip['trip_id']}/cancel", timeout=4)
        except Exception:
            pass
        self._notify("Trip canceled")
        self.current_trip = None
        self.root.current = "client_home"

    def voice_request(self):
        self._notify("Voice request placeholder — integrate speech-to-text service here.")

    # ---------- Driver flow ----------
    def start_driver(self):
        car_model_text = self.root.get_screen("driver_home").ids.car_model.text or ""
        if not car_model_text.strip():
            self._notify("Write the car model (e.g., 2015)")
            return
        try:
            car_model = int(car_model_text)
        except Exception:
            self._notify("The car model must be a number")
            return

        payload = {"name": self.user.get("name") if self.user else "Driver", "phone": self.user.get("phone") if self.user else "000", "role": "driver",
                   "car_model": car_model, "car_type": "new" if car_model >= 2010 else "old"}
        try:
            requests.post(f"{self.BACKEND}/register", json=payload, timeout=6)
        except Exception as e:
            print("Driver register failed:", e)

        driver_id = self.user.get("user_id") if self.user else random.randint(1000, 9999)

        threading.Thread(target=self._ws_driver_listener_thread, args=(driver_id,), daemon=True).start()

        self._driver_location_thread_stop.clear()
        self._driver_location_thread = threading.Thread(target=self._driver_location_sender_thread, args=(driver_id,), daemon=True)
        self._driver_location_thread.start()
        self._notify("Started receiving trips and sending location updates")


    def _ws_driver_listener_thread(self, driver_id):
        ws_url = f"{self.WS_BASE}/ws/driver/{driver_id}"
        try:
            ws = create_connection(ws_url, timeout=6)
            self.driver_ws = ws
        except Exception as e:
            print("WS connect error (driver):", e)
            # if no ws, driver will refresh pending trips via REST endpoint manually (open_driver_trips)
            return

        try:
            while True:
                try:
                    msg = ws.recv()
                except WebSocketConnectionClosedException:
                    break
                if not msg:
                    continue
                try:
                    data = json.loads(msg)
                except Exception:
                    continue
                # expect {"event":"new_trip","data":{...}}
                if data.get("event") == "new_trip":
                    trip = data.get("data", {})
                    Clock.schedule_once(lambda dt, t=trip: self._incoming_trip_dialog(t))
        finally:
            try:
                ws.close()
            except Exception:
                pass

    def _incoming_trip_dialog(self, trip):
        title = f"A new trip #{trip.get('trip_id', random.randint(100,999))}"
        from_info = trip.get("from_lat"), trip.get("from_lng")
        to_info = trip.get("to_lat"), trip.get("to_lng")
        content = f"from: {from_info}\nto: {to_info}\nprice: {trip.get('price', 'Unknown')}"
        dlg = MDDialog(title=title, text=content, buttons=[
            MDFlatButton(text="Refuse", on_release=lambda x: self._driver_reject(trip, dlg)),
            MDRaisedButton(text="Accept", on_release=lambda x: self._driver_accept(trip, dlg))
        ])
        dlg.open()

    def _driver_accept(self, trip, dlg):
        try:
            requests.post(f"{self.BACKEND}/trips/{trip.get('trip_id')}/complete", json={"status": "accepted"}, timeout=6)
        except Exception:
            pass
        try:
            dlg.dismiss()
        except Exception:
            pass
        # increment UI counter
        try:
            lbl = self.root.get_screen("driver_home").ids.driver_status
            text = lbl.text
            n = int(text.split(":")[-1].strip())
        except Exception:
            n = 0
        n += 1
        try:
            self.root.get_screen("driver_home").ids.driver_status.text = f"Accepted trips: {n}"
        except Exception:
            pass

        # set current trip and go to driver tracking
        self.current_trip = trip
        Clock.schedule_once(lambda dt: self._open_driver_tracking(trip), 0.3)
        self._notify("Trip accepted — move to tracking")

    def _driver_reject(self, trip, dlg):
        try:
            requests.post(f"{self.BACKEND}/trips/{trip.get('trip_id')}/complete", json={"status": "rejected"}, timeout=6)
        except Exception:
            pass
        try:
            dlg.dismiss()
        except Exception:
            pass
        self._notify("Trip rejected")

    def open_driver_trips(self):
        # fetch pending trips from backend and show
        try:
            r = requests.get("http://127.0.0.1:8000/trips/pending", timeout=5)
            data = r.json()
            trips = data.get("trips", [])
        except Exception as e:
            self._notify(f"Failed to load trips: {e}")
            trips = []
        # populate list
        lst = self.root.get_screen("driver_trips").ids.pending_list
        lst.clear_widgets()
        from kivymd.uix.list import OneLineAvatarIconListItem
        for t in trips:
            text = f"#{t['id']} - client {t['client_id']} | {t.get('price','-')} ج"
            item = OneLineAvatarIconListItem(text=text)
            acc = MDRaisedButton(text="Accept", size_hint=(None,None), size=(dp(70), dp(36)))
            rej = MDFlatButton(text="Reject")
            def make_accept(tid): return lambda *a: self._accept_trip_by_driver(tid)
            def make_reject(tid): return lambda *a: self._reject_trip_by_driver(tid)
            acc.bind(on_release=make_accept(t['id']))
            rej.bind(on_release=make_reject(t['id']))
            from kivy.uix.boxlayout import BoxLayout
            box = BoxLayout(size_hint_x=None, width=200)
            box.add_widget(acc); box.add_widget(rej)
            item.add_widget(box)
            lst.add_widget(item)

        self.root.current = "driver_trips"

    def _accept_trip_by_driver(self, trip_id):
        try:
            requests.post(f"{self.BACKEND}/trips/{trip_id}/complete", json={"status": "accepted"}, timeout=6)
            self._notify("Trip accepted")
            self.open_driver_trips()
        except Exception as e:
            self._notify(f"Failed to accept trip: {e}")

    def _reject_trip_by_driver(self, trip_id):
        try:
            requests.post(f"{self.BACKEND}/trips/{trip_id}/complete", json={"status": "rejected"}, timeout=6)
            self._notify("Trip rejected")
            self.open_driver_trips()
        except Exception as e:
            self._notify(f"Failed to reject trip: {e}")

    def _open_driver_tracking(self, trip):
        try:
            screen = self.root.get_screen("driver_tracking")
            driver_lat = trip.get("driver_lat", trip.get("from_lat", 30.0460))
            driver_lng = trip.get("driver_lng", trip.get("from_lng", 31.2350))
            screen.ids.driver_map.center_on(driver_lat, driver_lng)
            # driver marker
            try:
                screen.ids.driver_map.remove_widget(self.driver_marker)
            except Exception:
                pass
            self.driver_marker = MapMarker(lat=driver_lat, lon=driver_lng)
            screen.ids.driver_map.add_widget(self.driver_marker)
            # client marker
            try:
                screen.ids.driver_map.remove_widget(self.client_marker)
            except Exception:
                pass
            client_lat = trip.get("from_lat", 30.0444)
            client_lng = trip.get("from_lng", 31.2357)
            self.client_marker = MapMarker(lat=client_lat, lon=client_lng)
            screen.ids.driver_map.add_widget(self.client_marker)
            self.root.current = "driver_tracking"
            # start simulated movement thread to move driver towards client (if not already running)
            if not self._driver_location_thread or not self._driver_location_thread.is_alive():
                self._driver_location_thread_stop.clear()
                self._driver_location_thread = threading.Thread(target=self._driver_location_sender_thread, args=(self.user.get("user_id") if self.user else 0,), daemon=True)
                self._driver_location_thread.start()
        except Exception as e:
            print("open driver tracking error:", e)

    def _driver_location_sender_thread(self, driver_id):
        """Continuously send driver location to backend (or simulate locally)"""
        # If driver accepted a trip and has client marker, move toward client and POST location to backend
        while not self._driver_location_thread_stop.is_set():
            try:
                if self.driver_marker and self.client_marker and self.current_trip:
                    # move fractionally toward client
                    dlat = (self.client_marker.lat - self.driver_marker.lat) * 0.25
                    dlng = (self.client_marker.lon - self.driver_marker.lon) * 0.25
                    newlat = self.driver_marker.lat + dlat
                    newlon = self.driver_marker.lon + dlng
                    # update own UI
                    Clock.schedule_once(lambda dt, a=newlat, b=newlon: self._move_driver_local(a, b))
                    # send to backend location endpoint
                    try:
                        loc_payload = {"driver_id": driver_id, "lat": newlat, "lng": newlon}
                        requests.post(f"{self.BACKEND}/drivers/{driver_id}/location", json=loc_payload, timeout=4)
                    except Exception:
                        pass
                else:
                    # random small heartbeat location
                    newlat = 30.0444 + random.uniform(-0.005, 0.005)
                    newlon = 31.2357 + random.uniform(-0.005, 0.005)
                    Clock.schedule_once(lambda dt, a=newlat, b=newlon: self._move_driver_local(a, b))
                    try:
                        loc_payload = {"driver_id": driver_id, "lat": newlat, "lng": newlon}
                        requests.post(f"{self.BACKEND}/drivers/{driver_id}/location", json=loc_payload, timeout=4)
                    except Exception:
                        pass
                time.sleep(2)
            except Exception as e:
                print("driver location sender err:", e)
                time.sleep(2)

    def _move_driver_local(self, lat, lon):
        # update driver marker on both driver and client maps if present
        try:
            if self.driver_marker:
                try:
                    # driver_marker may belong to driver_map or tracking_map
                    parent = self.driver_marker.parent
                    if parent:
                        parent.remove_widget(self.driver_marker)
                except Exception:
                    pass
            self.driver_marker = MapMarker(lat=lat, lon=lon)
            # add to driver_map if current screen is driver_tracking else to client tracking
            if self.root.current == "driver_tracking":
                try:
                    self.root.get_screen("driver_tracking").ids.driver_map.add_widget(self.driver_marker)
                except Exception:
                    pass
            if self.root.current == "client_tracking":
                try:
                    self.root.get_screen("client_tracking").ids.tracking_map.add_widget(self.driver_marker)
                except Exception:
                    pass
        except Exception as e:
            print("move driver local err:", e)

    def driver_start_ride(self):
        # driver indicates "start ride" — calculate best route (call backend /route optionally)
        self._notify("Driver started the ride — calculating route (simulated).")
        # In a real app, contact backend /route to get polyline and send to clients via ws.

    def driver_end_ride(self):
        if not self.current_trip:
            self._notify("No active trip")
            return
        price = self.current_trip.get("price", 100)
        try:
            # inform backend the trip is finished
            requests.post(f"{self.BACKEND}/trips/{self.current_trip['trip_id']}/finish", json={"price": price}, timeout=6)
        except Exception:
            pass
        Clock.schedule_once(lambda dt: self._open_payment_screen(price), 0.2)
        self._notify("Ride finished. Showing payment.")

    # ---------- Payment ----------
    def _open_payment_screen(self, price):
        try:
            self.root.get_screen("payment").ids.final_price.text = f"price: {price} ج"
            self.root.current = "payment"
            # reset current trip
            self.current_trip = None
        except Exception as e:
            print("open payment err:", e)

    def pay(self, method: str):
        if method == "card":
            self._notify("Processing card payment (simulated)...")
        else:
            self._notify("Cash payment selected")
        Clock.schedule_once(lambda dt: setattr(self.root, 'current', 'client_home'), 1.2)

    # ---------- SOS & Chatbot ----------
    def sos_dialog(self):
        from kivymd.uix.textfield import MDTextField
        box = BoxLayout(orientation="vertical", spacing=dp(8))
        msg = MDTextField(hint_text="Write your message here")
        box.add_widget(msg)
        dlg = MDDialog(title="SOS button", type="custom", content_cls=box,
                       buttons=[MDFlatButton(text="cancel", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="send", on_release=lambda x: self._send_sos(msg.text, dlg))])
        dlg.open()

    def _send_sos(self, message: str, dlg: MDDialog):
        dlg.dismiss()
        try:
            requests.post(f"{self.BACKEND}/sos", json={"msg": message}, timeout=6)
            self._notify("The distress call was sent to the administration.")
        except Exception as e:
            self._notify(f"Transmission failed: {e}")

    def open_chatbot(self):
        from kivymd.uix.textfield import MDTextField
        box = BoxLayout(orientation="vertical", spacing=dp(8))
        msg = MDTextField(hint_text="Ask me anything")
        box.add_widget(msg)
        dlg = MDDialog(title="Smart assistant", type="custom", content_cls=box,
                       buttons=[MDFlatButton(text="close", on_release=lambda x: dlg.dismiss()),
                                MDRaisedButton(text="send", on_release=lambda x: self._send_chat(msg.text))])
        dlg.open()

    def _send_chat(self, text: str):
        try:
            r = requests.post(f"{self.BACKEND}/chatbot", json={"text": text}, timeout=6)
            data = r.json()
            self._notify(data.get("reply", "No reply"))
        except Exception as e:
            self._notify(str(e))


    

        
    # ---------- Account / UI helpers ----------
    def open_account(self):
        if not self.user:
            self._notify("You are not logged in yet")
            return
        text = f"name: {self.user.get('name')}\\nID: {self.user.get('user_id')}\\nRole: {self.role}"
        dlg = MDDialog(title="Account", text=text, buttons=[MDFlatButton(text="close", on_release=lambda x: dlg.dismiss())])
        dlg.open()

    def open_offers(self):
        content = BoxLayout(orientation="vertical", spacing=dp(8))
        b1 = MDRaisedButton(text="Monthly subscription - 300 ج", on_release=lambda *a: self._notify("Activated monthly subscription (simulation)"))
        b2 = MDRaisedButton(text="Quarterly subscription - 800 ج", on_release=lambda *a: self._notify("Activated quarterly subscription (simulation)"))
        content.add_widget(b1); content.add_widget(b2)
        dlg = MDDialog(title="Offers", type="custom", content_cls=content, buttons=[MDFlatButton(text="close", on_release=lambda x: dlg.dismiss())])
        dlg.open()

    def open_help(self):
        txt = "Help:\n- Emergency button\n- Chatbot\n- Route identification (simulated)\n- Payment simulation"
        self._notify(txt)

    def _notify(self, text: str):
        if self.dialog:
            try:
                self.dialog.dismiss()
            except Exception:
                pass
        if not text:
            text = "An unexpected error occurred"
        self.dialog = MDDialog(title="Notification", text=str(text),
                               buttons=[MDFlatButton(text="close", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def send_otp(self, phone_number):
        import requests
        url = "http://127.0.0.1:8000/send-otp"
        res = requests.post(url, json={"phone": phone_number})
        if res.status_code == 200:
            self.show_dialog("Verification", "OTP sent successfully.")
        else:
            self.show_dialog("Error", "Failed to send OTP.")

    def verify_otp(self, phone_number, entered_code):
        import requests
        url = "http://127.0.0.1:8000/verify-otp"
        res = requests.post(url, json={"phone": phone_number, "code": entered_code})
        if res.status_code == 200:
            self.show_dialog("Success", "Phone verified successfully.")
            Clock.schedule_once(lambda dt: setattr(self.root, "current", "terms"), 1)
        else:
            self.show_dialog("Error", "Invalid verification code.")


    # ---------- App shutdown helpers ----------
    def on_stop(self):
        # stop background threads
        try:
            self._driver_location_thread_stop.set()
        except Exception:
            pass
        try:
            if self.client_ws:
                self.client_ws.close()
            if self.driver_ws:
                self.driver_ws.close()
        except Exception:
            pass

if __name__ == "__main__":
    TaxiApp().run()
