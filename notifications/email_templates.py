"""
Email Templates for Appointment Notifications
Professional HTML email templates for various appointment-related communications
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class EmailTemplateManager:
    """Manages email templates for appointment notifications"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load all email templates"""
        return {
            'appointment_confirmation': {
                'subject': 'Appointment Confirmed - {formatted_datetime}',
                'html': self._get_confirmation_template(),
                'text': self._get_confirmation_text_template()
            },
            'appointment_reminder_24h': {
                'subject': 'Appointment Reminder - Tomorrow at {appointment_time}',
                'html': self._get_reminder_24h_template(),
                'text': self._get_reminder_24h_text_template()
            },
            'appointment_reminder_2h': {
                'subject': 'Appointment Reminder - In 2 Hours',
                'html': self._get_reminder_2h_template(),
                'text': self._get_reminder_2h_text_template()
            },
            'appointment_reminder_30m': {
                'subject': 'Appointment Reminder - In 30 Minutes',
                'html': self._get_reminder_30m_template(),
                'text': self._get_reminder_30m_text_template()
            },
            'appointment_follow_up': {
                'subject': 'Follow-up: Your Recent Appointment',
                'html': self._get_follow_up_template(),
                'text': self._get_follow_up_text_template()
            },
            'appointment_cancellation': {
                'subject': 'Appointment Cancelled - {formatted_datetime}',
                'html': self._get_cancellation_template(),
                'text': self._get_cancellation_text_template()
            },
            'appointment_rescheduling': {
                'subject': 'Appointment Rescheduled - New Time: {formatted_datetime}',
                'html': self._get_rescheduling_template(),
                'text': self._get_rescheduling_text_template()
            }
        }
    
    def get_template(self, template_name: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Get formatted template with context data"""
        try:
            template = self.templates.get(template_name)
            if not template:
                logger.error(f"Template {template_name} not found")
                return self._get_default_template(context)
            
            return {
                'subject': template['subject'].format(**context),
                'html': template['html'].format(**context),
                'text': template['text'].format(**context)
            }
        except Exception as e:
            logger.error(f"Error formatting template {template_name}: {str(e)}")
            return self._get_default_template(context)
    
    def _get_default_template(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Get default template when specific template fails"""
        return {
            'subject': 'Appointment Notification',
            'html': f"""
            <html>
                <body>
                    <h2>Appointment Notification</h2>
                    <p>You have an appointment notification.</p>
                    <p>Appointment Details:</p>
                    <ul>
                        <li>Date: {context.get('appointment_date', 'N/A')}</li>
                        <li>Time: {context.get('appointment_time', 'N/A')}</li>
                        <li>Provider: Dr. {context.get('provider_name', 'N/A')}</li>
                    </ul>
                </body>
            </html>
            """,
            'text': f"Appointment notification for {context.get('formatted_datetime', 'your appointment')}"
        }
    
    def _get_confirmation_template(self) -> str:
        """Appointment confirmation email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Appointment Confirmed</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c5aa0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .appointment-card {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2c5aa0; }}
                .detail-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #2c5aa0; }}
                .value {{ margin-left: 10px; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
                .button {{ display: inline-block; background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                .success-icon {{ color: #28a745; font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><span class="success-icon">✓</span> Appointment Confirmed</h1>
                    <p>Your appointment has been successfully scheduled</p>
                </div>
                
                <div class="content">
                    <p>Dear {patient_name},</p>
                    
                    <p>We're pleased to confirm your upcoming appointment. Please find the details below:</p>
                    
                    <div class="appointment-card">
                        <h3>Appointment Details</h3>
                        <div class="detail-row">
                            <span class="label">Date & Time:</span>
                            <span class="value">{formatted_datetime}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Provider:</span>
                            <span class="value">Dr. {provider_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Appointment Type:</span>
                            <span class="value">{appointment_type}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Duration:</span>
                            <span class="value">{duration} minutes</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Location:</span>
                            <span class="value">{location}</span>
                        </div>
                        {notes}
                    </div>
                    
                    <h3>What to Expect</h3>
                    <ul>
                        <li>Please arrive 15 minutes early for check-in</li>
                        <li>Bring a valid ID and insurance card</li>
                        <li>Bring a list of current medications</li>
                        <li>Prepare any questions you'd like to discuss</li>
                    </ul>
                    
                    <h3>Need to Make Changes?</h3>
                    <p>If you need to reschedule or cancel your appointment, please contact us at least 24 hours in advance.</p>
                    
                    <div style="text-align: center;">
                        <a href="#" class="button">View Appointment Details</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Thank you for choosing our healthcare services.</p>
                    <p>If you have any questions, please don't hesitate to contact us.</p>
                    <p><strong>MediRemind Healthcare</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_confirmation_text_template(self) -> str:
        """Text version of confirmation template"""
        return """
        APPOINTMENT CONFIRMED
        
        Dear {patient_name},
        
        Your appointment has been successfully scheduled:
        
        Date & Time: {formatted_datetime}
        Provider: Dr. {provider_name}
        Appointment Type: {appointment_type}
        Duration: {duration} minutes
        Location: {location}
        
        Please arrive 15 minutes early and bring:
        - Valid ID and insurance card
        - List of current medications
        - Any questions you'd like to discuss
        
        If you need to make changes, please contact us at least 24 hours in advance.
        
        Thank you for choosing MediRemind Healthcare.
        """
    
    def _get_reminder_24h_template(self) -> str:
        """24-hour reminder template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Appointment Reminder</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .appointment-card {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9800; }}
                .detail-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #ff9800; }}
                .value {{ margin-left: 10px; }}
                .reminder-icon {{ color: #ff9800; font-size: 24px; }}
                .button {{ display: inline-block; background-color: #ff9800; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><span class="reminder-icon">🔔</span> Appointment Reminder</h1>
                    <p>Your appointment is tomorrow</p>
                </div>
                
                <div class="content">
                    <p>Dear {patient_name},</p>
                    
                    <p>This is a friendly reminder that you have an appointment scheduled for tomorrow.</p>
                    
                    <div class="appointment-card">
                        <h3>Tomorrow's Appointment</h3>
                        <div class="detail-row">
                            <span class="label">Date & Time:</span>
                            <span class="value">{formatted_datetime}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Provider:</span>
                            <span class="value">Dr. {provider_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Location:</span>
                            <span class="value">{location}</span>
                        </div>
                    </div>
                    
                    <h3>Preparation Checklist</h3>
                    <ul>
                        <li>✓ Confirm transportation arrangements</li>
                        <li>✓ Gather required documents (ID, insurance card)</li>
                        <li>✓ Prepare list of current medications</li>
                        <li>✓ Write down any questions or concerns</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="#" class="button">View Full Details</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_reminder_24h_text_template(self) -> str:
        """Text version of 24-hour reminder"""
        return """
        APPOINTMENT REMINDER - TOMORROW
        
        Dear {patient_name},
        
        This is a reminder that you have an appointment tomorrow:
        
        Date & Time: {formatted_datetime}
        Provider: Dr. {provider_name}
        Location: {location}
        
        Please remember to:
        - Arrive 15 minutes early
        - Bring ID and insurance card
        - Bring list of current medications
        
        See you tomorrow!
        MediRemind Healthcare
        """
    
    def _get_reminder_2h_template(self) -> str:
        """2-hour reminder template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Appointment in 2 Hours</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .appointment-card {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f44336; }}
                .urgent {{ color: #f44336; font-weight: bold; }}
                .clock-icon {{ color: #f44336; font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><span class="clock-icon">⏰</span> Appointment in 2 Hours</h1>
                    <p class="urgent">Time to start preparing!</p>
                </div>
                
                <div class="content">
                    <p>Dear {patient_name},</p>
                    
                    <p>Your appointment with Dr. {provider_name} is in <strong>2 hours</strong>.</p>
                    
                    <div class="appointment-card">
                        <h3>Appointment Details</h3>
                        <p><strong>Time:</strong> {appointment_time}</p>
                        <p><strong>Location:</strong> {location}</p>
                        <p><strong>Provider:</strong> Dr. {provider_name}</p>
                    </div>
                    
                    <h3>Final Reminders</h3>
                    <ul>
                        <li>Leave with enough time to arrive 15 minutes early</li>
                        <li>Double-check you have your ID and insurance card</li>
                        <li>Consider traffic and parking time</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_reminder_2h_text_template(self) -> str:
        """Text version of 2-hour reminder"""
        return """
        APPOINTMENT IN 2 HOURS
        
        Dear {patient_name},
        
        Your appointment with Dr. {provider_name} is in 2 hours at {appointment_time}.
        
        Location: {location}
        
        Please start preparing and allow extra time for travel.
        
        MediRemind Healthcare
        """
    
    def _get_reminder_30m_template(self) -> str:
        """30-minute reminder template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Appointment in 30 Minutes</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #e91e63; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .urgent-card {{ background-color: #fff3e0; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #e91e63; }}
                .urgent {{ color: #e91e63; font-weight: bold; font-size: 18px; }}
                .alarm-icon {{ color: #e91e63; font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><span class="alarm-icon">🚨</span> Appointment in 30 Minutes</h1>
                    <p class="urgent">Time to head out!</p>
                </div>
                
                <div class="content">
                    <p>Dear {patient_name},</p>
                    
                    <div class="urgent-card">
                        <p class="urgent">Your appointment is starting soon!</p>
                        <p><strong>Time:</strong> {appointment_time}</p>
                        <p><strong>Location:</strong> {location}</p>
                        <p><strong>Provider:</strong> Dr. {provider_name}</p>
                    </div>
                    
                    <p>If you haven't left yet, please head out now to arrive on time.</p>
                    
                    <p>We look forward to seeing you!</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_reminder_30m_text_template(self) -> str:
        """Text version of 30-minute reminder"""
        return """
        APPOINTMENT IN 30 MINUTES!
        
        Dear {patient_name},
        
        Your appointment with Dr. {provider_name} starts in 30 minutes at {appointment_time}.
        
        Location: {location}
        
        Please head out now if you haven't already!
        
        MediRemind Healthcare
        """
    
    def _get_follow_up_template(self) -> str:
        """Follow-up email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Follow-up: Your Recent Appointment</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4caf50; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .feedback-card {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50; }}
                .button {{ display: inline-block; background-color: #4caf50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .heart-icon {{ color: #4caf50; font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><span class="heart-icon">💚</span> Thank You for Your Visit</h1>
                    <p>We hope your appointment went well</p>
                </div>
                
                <div class="content">
                    <p>Dear {patient_name},</p>
                    
                    <p>Thank you for visiting us for your recent appointment with Dr. {provider_name}. We hope everything went well and that you received the care you needed.</p>
                    
                    <div class="feedback-card">
                        <h3>How Was Your Experience?</h3>
                        <p>Your feedback helps us improve our services. We'd love to hear about your experience.</p>
                        
                        <div style="text-align: center;">
                            <a href="#" class="button">Leave Feedback</a>
                            <a href="#" class="button">Schedule Follow-up</a>
                        </div>
                    </div>
                    
                    <h3>Next Steps</h3>
                    <ul>
                        <li>Follow any instructions provided by Dr. {provider_name}</li>
                        <li>Take medications as prescribed</li>
                        <li>Schedule any recommended follow-up appointments</li>
                        <li>Contact us if you have any questions or concerns</li>
                    </ul>
                    
                    <p>If you need to reach us, please don't hesitate to contact our office.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_follow_up_text_template(self) -> str:
        """Text version of follow-up template"""
        return """
        FOLLOW-UP: YOUR RECENT APPOINTMENT
        
        Dear {patient_name},
        
        Thank you for your recent appointment with Dr. {provider_name}. We hope everything went well.
        
        Please remember to:
        - Follow any instructions provided
        - Take medications as prescribed
        - Schedule follow-up appointments if recommended
        
        We'd love your feedback on your experience. Contact us if you have any questions.
        
        MediRemind Healthcare
        """
    
    def _get_cancellation_template(self) -> str:
        """Cancellation email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Appointment Cancelled</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #9e9e9e; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .cancellation-card {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #9e9e9e; }}
                .button {{ display: inline-block; background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                .cancel-icon {{ color: #9e9e9e; font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><span class="cancel-icon">❌</span> Appointment Cancelled</h1>
                    <p>Your appointment has been cancelled</p>
                </div>
                
                <div class="content">
                    <p>Dear {patient_name},</p>
                    
                    <p>We're writing to confirm that your appointment has been cancelled as requested.</p>
                    
                    <div class="cancellation-card">
                        <h3>Cancelled Appointment</h3>
                        <p><strong>Date & Time:</strong> {formatted_datetime}</p>
                        <p><strong>Provider:</strong> Dr. {provider_name}</p>
                        <p><strong>Appointment Type:</strong> {appointment_type}</p>
                    </div>
                    
                    <h3>Need to Reschedule?</h3>
                    <p>If you'd like to schedule a new appointment, we're here to help. Please contact us or use our online booking system.</p>
                    
                    <div style="text-align: center;">
                        <a href="#" class="button">Schedule New Appointment</a>
                    </div>
                    
                    <p>Thank you for letting us know about the cancellation in advance.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_cancellation_text_template(self) -> str:
        """Text version of cancellation template"""
        return """
        APPOINTMENT CANCELLED
        
        Dear {patient_name},
        
        Your appointment has been cancelled:
        
        Date & Time: {formatted_datetime}
        Provider: Dr. {provider_name}
        Appointment Type: {appointment_type}
        
        If you need to reschedule, please contact us or use our online booking system.
        
        Thank you for the advance notice.
        
        MediRemind Healthcare
        """
    
    def _get_rescheduling_template(self) -> str:
        """Rescheduling email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Appointment Rescheduled</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .appointment-card {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9800; }}
                .button {{ display: inline-block; background-color: #ff9800; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                .reschedule-icon {{ color: #ff9800; font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><span class="reschedule-icon">📅</span> Appointment Rescheduled</h1>
                    <p>Your appointment has been moved to a new time</p>
                </div>
                
                <div class="content">
                    <p>Dear {patient_name},</p>
                    
                    <p>We're writing to confirm that your appointment has been successfully rescheduled.</p>
                    
                    <div class="appointment-card">
                        <h3>New Appointment Details</h3>
                        <p><strong>New Date & Time:</strong> {formatted_datetime}</p>
                        <p><strong>Provider:</strong> Dr. {provider_name}</p>
                        <p><strong>Location:</strong> {location}</p>
                        <p><strong>Appointment Type:</strong> {appointment_type}</p>
                    </div>
                    
                    <p>Please make note of the new date and time. We'll send you reminder notifications as the appointment approaches.</p>
                    
                    <div style="text-align: center;">
                        <a href="#" class="button">View Appointment Details</a>
                    </div>
                    
                    <p>Thank you for your flexibility, and we look forward to seeing you at the new time.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_rescheduling_text_template(self) -> str:
        """Text version of rescheduling template"""
        return """
        APPOINTMENT RESCHEDULED
        
        Dear {patient_name},
        
        Your appointment has been rescheduled:
        
        New Date & Time: {formatted_datetime}
        Provider: Dr. {provider_name}
        Location: {location}
        Appointment Type: {appointment_type}
        
        Please make note of the new time. We'll send reminder notifications as the appointment approaches.
        
        Thank you for your flexibility.
        
        MediRemind Healthcare
        """

# Global instance
email_template_manager = EmailTemplateManager()