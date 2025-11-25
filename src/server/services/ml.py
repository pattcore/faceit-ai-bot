import torch
import torch.nn as nn
import torchvision.transforms as transforms
from fastapi import UploadFile, HTTPException
from PIL import Image
import io
import logging
from pathlib import Path
from ..config.settings import settings

logger = logging.getLogger(__name__)


class MLService:
    def __init__(self):
        self.model = None
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])

    async def get_model(self) -> nn.Module:
        """Lazy loading of the model"""
        if self.model is None:
            try:
                # Ensure cache directory exists
                Path(settings.MODEL_CACHE_DIR).mkdir(
                    parents=True, exist_ok=True
                )

                self.model = torch.hub.load(
                    'pytorch/vision:v0.10.0',
                    'resnet18',
                    pretrained=True,
                    force_reload=False,
                    cache_dir=settings.MODEL_CACHE_DIR
                )
                self.model.eval()
            except Exception:
                logger.exception("Failed to load ML model")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to initialize ML model"
                )
        return self.model

    async def analyze_demo(self, file: UploadFile):
        """Analyze demo file using ML model"""
        filename = file.filename or ""

        if not filename.lower().endswith('.dem'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only .dem files are supported"
            )

        try:
            max_bytes = settings.MAX_DEMO_FILE_MB * 1024 * 1024

            contents = await file.read(max_bytes + 1)

            if len(contents) > max_bytes:
                logger.warning(
                    "Demo file too large: filename=%s size_bytes=%s limit_bytes=%s",
                    filename,
                    len(contents),
                    max_bytes,
                )
                raise HTTPException(
                    status_code=413,
                    detail="Demo file is too large",
                )

            header = contents[:4]
            suspicious_reason = None
            if header.startswith(b"MZ"):
                suspicious_reason = "PE executable signature (MZ) detected"
            elif header.startswith(b"PK"):
                suspicious_reason = "ZIP archive signature (PK) detected"
            elif header[:2] == b"\x1f\x8b":
                suspicious_reason = "GZIP archive signature detected"

            if suspicious_reason:
                logger.warning(
                    "Rejected demo upload due to suspicious header: filename=%s reason=%s",
                    filename,
                    suspicious_reason,
                )
                raise HTTPException(
                    status_code=400,
                    detail="Suspicious file content. Only raw .dem files are allowed",
                )

            image = Image.open(io.BytesIO(contents))

            model = await self.get_model()

            input_tensor = self.transform(image).unsqueeze(0)
            with torch.no_grad():
                output = model(input_tensor)

            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            predicted_idx = output.argmax(1).item()
            confidence = probabilities[predicted_idx].item()

            return {
                "filename": file.filename,
                "prediction": predicted_idx,
                "confidence": confidence,
            }

        except Exception as e:
            logger.exception("Failed to analyze demo")
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}"
            )
        finally:
            await file.close()
