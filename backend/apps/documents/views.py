from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from .models import Document
from .utils import DocumentProcessor

ocr_processor = DocumentProcessor()

@csrf_exempt
@require_POST
def upload_document(request):
    """
    Upload and process a document
    """
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)

        uploaded_file = request.FILES['file']
        document_type = request.POST.get('document_type', 'id_card')
        registration_id = request.POST.get('registration_id')

        if not registration_id:
            return JsonResponse({'error': 'Registration ID required'}, status=400)

        # Save the file
        file_name = default_storage.save(
            f'documents/{registration_id}/{uploaded_file.name}',
            ContentFile(uploaded_file.read())
        )

        # Create document record
        document = Document.objects.create(
            registration_id=registration_id,
            document_type=document_type,
            file_path=file_name,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            mime_type=uploaded_file.content_type
        )

        # Process with OCR
        ocr_result = ocr_processor.process_document(document)

        return JsonResponse({
            'document_id': document.id,
            'ocr_text': ocr_result.get('extracted_text', ''),
            'confidence': ocr_result.get('confidence', 0),
            'status': 'processed'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def verify_document(request, document_id):
    """
    Verify a document's authenticity
    """
    try:
        document = get_object_or_404(Document, id=document_id)

        # In a real implementation, this would use advanced verification
        # For now, return mock verification result
        verification_result = {
            'is_authentic': True,
            'confidence': 0.89,
            'checks_passed': ['format_check', 'content_check', 'security_features']
        }

        document.verification_status = 'verified' if verification_result['is_authentic'] else 'rejected'
        document.verification_confidence = verification_result['confidence']
        document.save()

        return JsonResponse(verification_result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def download_document(request, document_id):
    """
    Download a document file
    """
    try:
        document = get_object_or_404(Document, id=document_id)

        if not default_storage.exists(document.file_path):
            return JsonResponse({'error': 'File not found'}, status=404)

        file_content = default_storage.open(document.file_path).read()
        response = HttpResponse(file_content, content_type=document.mime_type)
        response['Content-Disposition'] = f'attachment; filename="{document.file_name}"'

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)