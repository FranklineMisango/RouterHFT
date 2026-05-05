// hft_smoke_test.cpp
// C++ smoke test for RouterHFT core timing, validation, and latency utilities.

#include <arpa/inet.h>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <regex>
#include <string>
#include <thread>
#include <vector>

using Clock = std::chrono::steady_clock;

static uint64_t now_ns()
{
  return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();
}

static bool is_valid_ip(const std::string &ip)
{
  sockaddr_in sa4{};
  sockaddr_in6 sa6{};
  return inet_pton(AF_INET, ip.c_str(), &(sa4.sin_addr)) == 1 ||
         inet_pton(AF_INET6, ip.c_str(), &(sa6.sin6_addr)) == 1;
}

struct ComplianceResult {
  std::string rule;
  bool passed;
  std::string message;
};

static std::vector<ComplianceResult> validate_research_operation(bool research_only,
                                                                 bool transparent_methodology,
                                                                 const std::string &target,
                                                                 const std::string &operation)
{
  std::vector<ComplianceResult> results;

  results.push_back({"Research Only", research_only, research_only ? "OK" : "Must be research only"});
  results.push_back({"Transparent Methodology", transparent_methodology,
                     transparent_methodology ? "OK" : "Methodology must be transparent"});
  results.push_back({"Valid Target", is_valid_ip(target),
                     is_valid_ip(target) ? "OK" : "Target must be a valid IP address"});
  results.push_back({"Allowed Operation", operation == "latency_research",
                     operation == "latency_research" ? "OK" : "Operation not permitted"});

  return results;
}

static void test_timestamp_precision()
{
  std::cout << "Testing high-precision timestamps... ";
  uint64_t start = now_ns();
  std::this_thread::sleep_for(std::chrono::milliseconds(1));
  uint64_t end = now_ns();

  uint64_t diff = end - start;
  if (diff == 0) {
    throw std::runtime_error("timestamp difference was zero");
  }

  std::cout << "PASS (" << diff << " ns)\n";
}

static void test_compliance()
{
  std::cout << "Testing compliance checks... ";
  auto results = validate_research_operation(true, true, "8.8.8.8", "latency_research");
  for (const auto &result : results) {
    if (!result.passed) {
      throw std::runtime_error("expected compliant operation to pass");
    }
  }

  auto violations = validate_research_operation(false, false, "300.300.300.300", "market_manipulation");
  int failed = 0;
  for (const auto &result : violations) {
    if (!result.passed) {
      ++failed;
    }
  }
  if (failed < 3) {
    throw std::runtime_error("expected multiple compliance violations");
  }

  std::cout << "PASS (" << failed << " violations detected)\n";
}

static void test_network_utils()
{
  std::cout << "Testing network utilities... ";
  if (!is_valid_ip("8.8.8.8") || !is_valid_ip("::1") || is_valid_ip("not.an.ip")) {
    throw std::runtime_error("IP validation failed");
  }

  uint64_t start_ns = 1'000'000'000ULL;
  uint64_t end_ns = 1'015'000'000ULL;
  double latency_us = static_cast<double>(end_ns - start_ns) / 1000.0;

  if (latency_us != 15000.0) {
    throw std::runtime_error("latency calculation failed");
  }

  std::cout << "PASS\n";
}

int main()
{
  try {
    std::cout << "RouterHFT C++ Smoke Test\n";
    test_timestamp_precision();
    test_compliance();
    test_network_utils();
    std::cout << "All C++ smoke tests passed.\n";
    return 0;
  } catch (const std::exception &ex) {
    std::cerr << "Smoke test failed: " << ex.what() << '\n';
    return 1;
  }
}
