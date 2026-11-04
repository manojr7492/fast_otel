import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, PaymentFailedException
from app.core.telemetry import get_tracer
from app.models.payment import PaymentStatus, PaymentTransaction
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentResponse, ProcessPaymentRequest, RefundPaymentRequest

tracer = get_tracer("payment_service")


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PaymentRepository(session)

    async def process_payment(self, payment_in: ProcessPaymentRequest) -> PaymentResponse:
        with tracer.start_as_current_span("payment.process") as span:
            span.set_attribute("order.uuid", payment_in.order_uuid)
            span.set_attribute("user.uuid", payment_in.user_uuid)
            span.set_attribute("payment.amount", float(payment_in.amount))
            span.set_attribute("payment.method", payment_in.payment_method.value)

            txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            span.set_attribute("payment.reference", txn_ref)

            # Gateway execution span
            with tracer.start_as_current_span("payment.gateway_charge") as gateway_span:
                gateway_span.set_attribute("gateway.provider", "mock_stripe_gateway")
                gateway_span.set_attribute("gateway.currency", payment_in.currency)

                # Simulated network/gateway processing delay
                await asyncio.sleep(0.05)

                if payment_in.simulate_failure:
                    gateway_span.set_attribute("gateway.status", "DECLINED")
                    error_msg = "Card declined: Simulated payment failure for testing."

                    failed_payment = PaymentTransaction(
                        order_uuid=payment_in.order_uuid,
                        user_uuid=payment_in.user_uuid,
                        amount=payment_in.amount,
                        currency=payment_in.currency,
                        payment_method=payment_in.payment_method,
                        provider="mock_stripe_gateway",
                        status=PaymentStatus.FAILED,
                        transaction_reference=txn_ref,
                        error_message=error_msg,
                    )
                    await self.repo.create(failed_payment)
                    await self.session.commit()
                    span.set_attribute("payment.status", "FAILED")
                    raise PaymentFailedException(
                        reason=error_msg,
                        details={"order_uuid": payment_in.order_uuid, "reference": txn_ref},
                    )

                gateway_span.set_attribute("gateway.status", "SUCCESS")
                auth_code = f"AUTH-{uuid.uuid4().hex[:8].upper()}"
                gateway_span.set_attribute("gateway.auth_code", auth_code)

            # Successful payment
            payment = PaymentTransaction(
                order_uuid=payment_in.order_uuid,
                user_uuid=payment_in.user_uuid,
                amount=payment_in.amount,
                currency=payment_in.currency,
                payment_method=payment_in.payment_method,
                provider="mock_stripe_gateway",
                status=PaymentStatus.COMPLETED,
                transaction_reference=txn_ref,
                error_message=None,
            )
            await self.repo.create(payment)
            await self.session.commit()
            await self.session.refresh(payment)

            span.set_attribute("payment.uuid", payment.uuid)
            span.set_attribute("payment.status", "COMPLETED")
            return PaymentResponse.model_validate(payment)

    async def get_payment(self, identifier: str) -> PaymentResponse:
        with tracer.start_as_current_span("payment.get") as span:
            span.set_attribute("payment.identifier", identifier)
            payment = await self.repo.get_by_uuid(identifier)
            if not payment:
                payment = await self.repo.get_by_order_uuid(identifier)
            if not payment:
                raise EntityNotFoundException("PaymentTransaction", identifier)
            return PaymentResponse.model_validate(payment)

    async def refund_payment(
        self, payment_uuid: str, refund_in: RefundPaymentRequest
    ) -> PaymentResponse:
        with tracer.start_as_current_span("payment.refund") as span:
            span.set_attribute("payment.uuid", payment_uuid)
            payment = await self.repo.get_by_uuid(payment_uuid)
            if not payment:
                raise EntityNotFoundException("PaymentTransaction", payment_uuid)

            with tracer.start_as_current_span("payment.gateway_refund"):
                await asyncio.sleep(0.05)
                payment.status = PaymentStatus.REFUNDED
                payment.error_message = f"Refunded: {refund_in.reason}"

            await self.session.commit()
            await self.session.refresh(payment)
            span.set_attribute("payment.status", "REFUNDED")
            return PaymentResponse.model_validate(payment)

