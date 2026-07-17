# lambda_function.py
import json
import io
import base64
import logging
import sys
import traceback
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda function to generate invoice PDF and return as base64 encoded string
    """
    
    logger.info(f"Lambda invoked")
    
    try:
        # Get invoice data from event
        if 'body' in event:
            body = json.loads(event['body'])
            invoice_data = body.get('invoice_data', {})
        else:
            invoice_data = event.get('invoice_data', {})
        
        # For API Gateway proxy integration
        if event.get('httpMethod'):
            body = json.loads(event.get('body', '{}'))
            invoice_data = body.get('invoice_data', {})
        
        logger.info(f"Invoice data received")
        
        if not invoice_data:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing invoice_data'})
            }
        
        # Validate required fields
        required_fields = ['invoice_number', 'customer_name', 'cost']
        for field in required_fields:
            if field not in invoice_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Missing required field: {field}'})
                }
        
        # Generate PDF
        logger.info("Generating PDF...")
        pdf_buffer = generate_invoice_pdf(invoice_data)
        pdf_bytes = pdf_buffer.getvalue()
        
        logger.info(f"PDF generated, size: {len(pdf_bytes)} bytes")
        
        # Encode PDF to base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Generate filename
        filename = f"invoice_{invoice_data.get('invoice_number', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Return PDF as JSON with base64 encoded body
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'pdf_base64': pdf_base64,
                'filename': filename,
                'message': 'Invoice generated successfully'
            })
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Invalid JSON payload: {str(e)}'
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating invoice: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'trace': traceback.format_exc()
            })
        }


def generate_invoice_pdf(invoice_data):
    """
    Generate PDF invoice using reportlab
    """
    buffer = io.BytesIO()
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4A6CF7'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1A1A2E'),
            spaceAfter=10
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        value_style = ParagraphStyle(
            'ValueStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#1A1A2E'),
            spaceAfter=6
        )
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#9CA3AF'),
            alignment=TA_CENTER
        )
        
        # Build PDF content
        story = []
        
        # Header
        story.append(Paragraph("VEHICLE SERVICE INVOICE", title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4A6CF7')))
        story.append(Spacer(1, 20))
        
        # Invoice Details
        invoice_number = invoice_data.get('invoice_number', 'INV-001')
        invoice_date = invoice_data.get('service_date', datetime.now().strftime('%Y-%m-%d'))
        
        story.append(Paragraph(f"Invoice #: {invoice_number}", normal_style))
        story.append(Paragraph(f"Date: {invoice_date}", normal_style))
        story.append(Spacer(1, 15))
        
        # Customer Details
        story.append(Paragraph("Customer Details", heading_style))
        story.append(Paragraph(f"Name: {invoice_data.get('customer_name', 'N/A')}", value_style))
        story.append(Paragraph(f"Mobile: {invoice_data.get('customer_mobile', 'N/A')}", value_style))
        story.append(Paragraph(f"Address: {invoice_data.get('customer_address', 'N/A')}", value_style))
        story.append(Spacer(1, 15))
        
        # Vehicle Details
        story.append(Paragraph("Vehicle Details", heading_style))
        
        vehicle_data = [
            ['Vehicle Name', 'Brand', 'Model', 'Number'],
            [
                invoice_data.get('vehicle_name', 'N/A'),
                invoice_data.get('vehicle_brand', 'N/A'),
                invoice_data.get('vehicle_model', 'N/A'),
                invoice_data.get('vehicle_number', 'N/A')
            ]
        ]
        
        vehicle_table = Table(vehicle_data, colWidths=[100, 100, 100, 100])
        vehicle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1A1A2E')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(vehicle_table)
        story.append(Spacer(1, 15))
        
        # Problem Description
        story.append(Paragraph("Problem Description", heading_style))
        story.append(Paragraph(invoice_data.get('problem_description', 'N/A'), value_style))
        story.append(Spacer(1, 20))
        
        # Service Charges
        story.append(Paragraph("Service Charges", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB')))
        
        amount = invoice_data.get('cost', 0)
        
        charges_data = [
            ['Description', 'Amount'],
            ['Service Charges', f'₹ {amount:,.2f}'],
        ]
        
        charges_table = Table(charges_data, colWidths=[300, 100])
        charges_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1A1A2E')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(charges_table)
        story.append(Spacer(1, 10))
        
        # Total Amount
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB')))
        
        total_data = [
            ['TOTAL AMOUNT', f'₹ {amount:,.2f}']
        ]
        total_table = Table(total_data, colWidths=[300, 100])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4A6CF7')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(total_table)
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB')))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Thank you for choosing our service!", footer_style))
        story.append(Paragraph("Vehicle Service Management | www.vsm.com", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
    except Exception as e:
        logger.error(f"Error in generate_invoice_pdf: {str(e)}")
        raise
    
    return buffer