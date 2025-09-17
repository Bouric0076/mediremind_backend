# MediRemind Email Brand Guidelines

## Brand Identity

### Primary Colors
- **Primary Blue**: #2563EB (Medical trust and reliability)
- **Success Green**: #10B981 (Confirmations and positive actions)
- **Warning Orange**: #F59E0B (Rescheduling and important notices)
- **Error Red**: #EF4444 (Cancellations and urgent alerts)
- **Neutral Gray**: #6B7280 (Secondary text and borders)
- **Light Gray**: #F9FAFB (Background sections)

### Typography
- **Primary Font**: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- **Fallback**: Arial, sans-serif
- **Heading Sizes**: H1 (24px), H2 (20px), H3 (18px)
- **Body Text**: 16px
- **Small Text**: 14px
- **Line Height**: 1.6 for readability

### Logo and Branding
- **Brand Name**: MediRemind
- **Tagline**: "Your Health, Our Priority"
- **Logo Colors**: Primary Blue (#2563EB) with white text

## Email Design Principles

### Layout Structure
1. **Header Section**
   - Brand logo and name
   - Clear email purpose/title
   - Consistent color coding by email type

2. **Content Section**
   - Personalized greeting
   - Clear, scannable information
   - Prominent call-to-action buttons
   - Visual hierarchy with proper spacing

3. **Footer Section**
   - Contact information
   - Unsubscribe options
   - Legal disclaimers
   - Social media links

### Visual Hierarchy
- **Primary Information**: Large, bold text in primary color
- **Secondary Information**: Medium text in neutral color
- **Supporting Details**: Smaller text with adequate spacing
- **Action Items**: Prominent buttons with contrasting colors

### Accessibility Standards
- **Color Contrast**: Minimum 4.5:1 ratio for text
- **Font Size**: Minimum 14px for body text
- **Alt Text**: All images must have descriptive alt text
- **Screen Reader**: Semantic HTML structure

## Email Types and Color Coding

### Appointment Confirmations
- **Header Color**: Success Green (#10B981)
- **Tone**: Positive, reassuring
- **Key Elements**: Appointment details, preparation instructions

### Appointment Rescheduling
- **Header Color**: Warning Orange (#F59E0B)
- **Tone**: Informative, helpful
- **Key Elements**: New appointment details, reason for change

### Appointment Cancellations
- **Header Color**: Error Red (#EF4444)
- **Tone**: Apologetic, solution-oriented
- **Key Elements**: Cancellation reason, rebooking options

### Reminders
- **Header Color**: Primary Blue (#2563EB)
- **Tone**: Friendly, helpful
- **Key Elements**: Upcoming appointment details, preparation tips

## Personalization Guidelines

### Dynamic Content
- **Patient Name**: Always use first name for warmth
- **Doctor Information**: Include name, specialty, photo when available
- **Appointment Details**: Date, time, location with clear formatting
- **Custom Messages**: Tailored based on appointment type

### Contextual Information
- **Weather Updates**: For outdoor appointments
- **Preparation Instructions**: Specific to appointment type
- **Follow-up Actions**: Next steps after appointment

## Responsive Design

### Mobile Optimization
- **Single Column Layout**: Stack elements vertically
- **Touch-Friendly Buttons**: Minimum 44px height
- **Readable Text**: Minimum 16px on mobile
- **Optimized Images**: Compressed for fast loading

### Email Client Compatibility
- **Outlook Support**: Table-based layouts
- **Gmail Optimization**: Inline CSS styles
- **Apple Mail**: WebKit-specific enhancements
- **Dark Mode**: Adaptive color schemes

## Content Guidelines

### Tone of Voice
- **Professional yet Friendly**: Medical authority with human warmth
- **Clear and Concise**: Easy to scan and understand
- **Empathetic**: Understanding of patient concerns
- **Action-Oriented**: Clear next steps

### Message Structure
- **Subject Line**: Clear, specific, under 50 characters
- **Opening**: Personalized greeting
- **Body**: Key information in logical order
- **Closing**: Professional sign-off with contact info

### Legal and Compliance
- **HIPAA Compliance**: No sensitive medical information
- **Privacy Notice**: Link to privacy policy
- **Unsubscribe**: Clear opt-out mechanism
- **Contact Information**: Easy way to reach support

## Quality Assurance

### Testing Checklist
- [ ] Cross-client rendering
- [ ] Mobile responsiveness
- [ ] Accessibility compliance
- [ ] Link functionality
- [ ] Personalization accuracy
- [ ] Spam filter testing

### Performance Metrics
- **Open Rate**: Target 25-30%
- **Click-Through Rate**: Target 3-5%
- **Unsubscribe Rate**: Keep below 0.5%
- **Delivery Rate**: Maintain above 95%

## Implementation Notes

### Template Variables
- Use Django template syntax: `{{ variable_name }}`
- Implement fallbacks for missing data
- Validate all dynamic content

### Version Control
- Maintain template versioning
- A/B testing for improvements
- Regular review and updates

---

*Last Updated: January 2024*
*Version: 1.0*