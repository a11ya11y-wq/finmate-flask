import allure
import json


@allure.feature("Caching System")
@allure.story("Integration caching flow for categories")
class TestIntegrationCaching:

    @allure.title("Verify caching flow: hit, miss, and invalidation upon resource creation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_category_caching_flow(self, client, auth_headers, test_redis):
        # We know auth_headers creates a user with id=1
        user_id = 1
        cache_key = f"categories:{user_id}"

        with allure.step("Step 1: Verify cache is empty initially"):
            assert test_redis.get(cache_key) is None

        with allure.step("Step 2: Fetch categories to populate cache (Cache Miss)"):
            response = client.get("/api/v1/categories/all", headers=auth_headers)
            assert response.status_code == 200
            
            # Now Redis should contain the cached data
            cached_data = test_redis.get(cache_key)
            assert cached_data is not None, "Cache was not populated after GET request"
            
            # Optionally verify it's valid JSON
            parsed_cache = json.loads(cached_data)
            assert isinstance(parsed_cache, list)

        with allure.step("Step 3: Update a category to trigger cache invalidation"):
            update_payload = {
                "name": "Updated Category",
            }
            response = client.put("/api/v1/categories/1", headers=auth_headers, json=update_payload)
            assert response.status_code == 200

        with allure.step("Step 4: Verify cache was invalidated"):
            # The cache key should no longer exist in Redis
            assert test_redis.get(cache_key) is None, "Cache was not invalidated after PUT request"

    @allure.title("Verify caching flow for dashboard invalidation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_dashboard_caching_flow(self, client, auth_headers, test_redis):
        user_id = 1
        # The dashboard caches with params, e.g. dashboard:1:month
        cache_key = f"dashboard:{user_id}:month"

        with allure.step("Step 1: Fetch dashboard data to populate cache"):
            response = client.get("/api/v1/dashboard/?period=month", headers=auth_headers)
            assert response.status_code == 200
            
            # Redis should contain the dashboard cache
            cached_data = test_redis.get(cache_key)
            assert cached_data is not None, "Dashboard cache was not populated"

        with allure.step("Step 2: Modify category to trigger dashboard cache invalidation"):
            update_payload = {
                "name": "Dashboard Trigger",
            }
            response = client.put("/api/v1/categories/2", headers=auth_headers, json=update_payload)
            assert response.status_code == 200

        with allure.step("Step 3: Verify dashboard cache was invalidated"):
            # Dashboard cache uses pattern invalidation, so dashboard:1:30 should be gone
            assert test_redis.get(cache_key) is None, "Dashboard cache was not invalidated"
