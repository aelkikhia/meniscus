
import falcon

from meniscus.api import abort
from meniscus.api import ApiResource
from meniscus.api import format_response_body
from meniscus.api import load_body
from meniscus.api.correlation.correlation_exceptions \
    import CoordinatorCommunicationError
from meniscus.api.correlation.correlation_exceptions \
    import MessageAuthenticationError
from meniscus.api.correlation.correlation_exceptions \
    import MessageValidationError
from meniscus.api.correlation.correlation_exceptions \
    import ResourceNotFoundError
from meniscus.api.correlation.correlation_process import CorrelationMessage
from meniscus.api.correlation.correlation_process import TenantIdentification
from meniscus.api.correlation.correlation_process \
    import validate_event_message_body
from meniscus.api.tenant.resources import MESSAGE_TOKEN


class PublishMessageResource(ApiResource):

    def _validate_req_body_on_post(self, body):
        """
        This method validates the on_post request body
        """
        try:
            validate_event_message_body(body)

        except MessageValidationError as ex:
            abort(falcon.HTTP_400, ex.message)

    def on_post(self, req, resp, tenant_id):
        """
        This method is passed log event data by a tenant. The request will
        have a message token and a tenant id which must be validated either
        by the local cache or by a call to this workers coordinator.
        """

        #read message token from header
        message_token = req.get_header(MESSAGE_TOKEN, required=True)

        #Validate the tenant's JSON event log data as valid JSON.
        body = load_body(req)
        self._validate_req_body_on_post(body)

        tenant_identification = TenantIdentification(
            tenant_id, message_token)

        try:
            tenant = tenant_identification.get_validated_tenant()
            message = CorrelationMessage(tenant, body)
            message.process_message()
            if message.is_durable():
                resp.status = falcon.HTTP_202
                resp.body = format_response_body(
                    message.get_durable_job_info())

            else:
                resp.status = falcon.HTTP_204

        except MessageAuthenticationError as ex:
            abort(falcon.HTTP_401, ex.message)
        except ResourceNotFoundError as ex:
            abort(falcon.HTTP_404, ex.message)
        except CoordinatorCommunicationError:
            abort(falcon.HTTP_500)
