from .handlers import admin_router, help_router, order_status_router, parameters_router, price_router, start_router, statistic_router, subscription_info_router



__all__ = [router for router in globals().keys() if router.endswith('router')]