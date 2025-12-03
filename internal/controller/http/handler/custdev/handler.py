from internal import interface
from pkg.log_wrapper import auto_log
from pkg.trace_wrapper import traced_method

import json
import csv
import io
import zipfile
import ast
from datetime import datetime
from fastapi.responses import StreamingResponse
from fastapi import HTTPException

from .model import *


class CustDevController(interface.ICustDevController):
    def __init__(
            self,
            tel: interface.ITelemetry,
            custdev_service: interface.ICustDevService
    ):
        self.tracer = tel.tracer()
        self.logger = tel.logger()
        self.custdev_service = custdev_service

    @traced_method()
    @auto_log()
    async def create_questions(self, body: CreateQuestionsRequest):
        questions_id = await self.custdev_service.create_questions(body.questions)
        return {"id": questions_id}

    @traced_method()
    @auto_log()
    async def create_questions_batch(self, body: CreateQuestionsBatchRequest):
        ids = await self.custdev_service.create_questions_batch(body.questions_list)
        return {"ids": ids}

    @traced_method()
    @auto_log()
    async def get_questions_by_id(self, questions_id: int):
        questions = (await self.custdev_service.get_questions_by_id(questions_id))[0]
        return {
            "id": questions.id,
            "questions": questions.questions
        }

    @traced_method()
    @auto_log()
    async def get_all_questions(self):
        questions_list = await self.custdev_service.get_all_questions()
        return {
            "questions": [
                {
                    "id": question.id,
                    "questions": question.questions
                }
                for question in questions_list
            ]
        }

    @traced_method()
    @auto_log()
    async def get_all_custdev(self):
        all_custdev = await self.custdev_service.get_all_custdev()
        return [
            {
                "id": custdev.id,
                "questions": (await self.custdev_service.get_questions_by_id(custdev.questions_id))[0].questions,
                "result": custdev.result
            }
            for custdev in all_custdev
        ]

    @traced_method()
    @auto_log()
    async def delete_questions(self, questions_id: int):
        await self.custdev_service.delete_questions(questions_id)
        return {"success": True}

    def _parse_custdev_result(self, result: str) -> list[dict]:
        """Парсит JSON из поля result в список вопрос-ответ."""
        try:
            # Пробуем сначала парсить как JSON
            data = json.loads(result)
            return data
        except json.JSONDecodeError:
            # Если не получилось, пробуем парсить как Python dict (старый формат)
            try:
                data = ast.literal_eval(result)
                if isinstance(data, list):
                    return data
                else:
                    raise ValueError(f"Unexpected data type: {type(data)}")
            except (ValueError, SyntaxError) as e:
                raise ValueError(f"Invalid custdev result format: {str(e)}")

    def _generate_csv_content(self, custdev_records: list[dict]) -> str:
        """Генерирует CSV контент с вопросами как заголовками."""
        if not custdev_records:
            return ""

        # Парсим все результаты
        parsed_records = []

        for record in custdev_records:
            try:
                qa_pairs = self._parse_custdev_result(record['result'])
                parsed_records.append({
                    'id': record['id'],
                    'qa_pairs': qa_pairs
                })
            except ValueError as e:
                self.logger.error(f"Error parsing custdev {record['id']}: {e}")
                continue

        if not parsed_records:
            return ""

        # Генерируем CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Для каждого custdev записываем вопросы как заголовки, ответы как значения
        for record in parsed_records:
            qa_pairs = record['qa_pairs']

            # Заголовки = текст вопросов
            headers = [qa_pair.get('question', '') for qa_pair in qa_pairs]
            writer.writerow(headers)

            # Значения = ответы
            answers = [qa_pair.get('answer', '') for qa_pair in qa_pairs]
            writer.writerow(answers)

            # Пустая строка между разными custdev записями
            if len(parsed_records) > 1:
                writer.writerow([])

        return output.getvalue()

    @traced_method()
    @auto_log()
    async def get_custdev_by_id_csv(self, custdev_id: int):
        """Экспорт одного custdev в CSV."""
        custdev_list = await self.custdev_service.get_custdev_by_id(custdev_id)

        if not custdev_list:
            raise HTTPException(status_code=404, detail=f"Custdev {custdev_id} not found")

        custdev = custdev_list[0]
        questions = (await self.custdev_service.get_questions_by_id(custdev.questions_id))[0]

        record = {
            "id": custdev.id,
            "questions": questions.questions,
            "result": custdev.result
        }

        try:
            csv_content = self._generate_csv_content([record])
        except Exception as e:
            self.logger.error(f"Error generating CSV for custdev {custdev_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"custdev_{custdev_id}_{timestamp}.csv"

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    @traced_method()
    @auto_log()
    async def export_all_custdev_csv(self):
        """Экспорт всех custdev в ZIP архив."""
        all_custdev = await self.custdev_service.get_all_custdev()

        if not all_custdev:
            raise HTTPException(status_code=404, detail="No custdev records found")

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for custdev in all_custdev:
                try:
                    questions = (await self.custdev_service.get_questions_by_id(custdev.questions_id))[0]

                    record = {
                        "id": custdev.id,
                        "questions": questions.questions,
                        "result": custdev.result
                    }

                    csv_content = self._generate_csv_content([record])
                    filename = f"custdev_{custdev.id}.csv"
                    zip_file.writestr(filename, csv_content)

                except Exception as e:
                    self.logger.error(f"Error processing custdev {custdev.id}: {e}")
                    continue

        zip_buffer.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"custdev_export_{timestamp}.zip"

        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )