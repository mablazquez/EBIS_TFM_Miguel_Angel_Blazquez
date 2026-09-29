package com.intelligentqa.sample.service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

public class OrderProcessingService {

    private static final BigDecimal VIP_DISCOUNT_RATE = new BigDecimal("0.15");
    private static final BigDecimal REGULAR_DISCOUNT_THRESHOLD = new BigDecimal("100.00");
    private static final BigDecimal REGULAR_DISCOUNT_RATE = new BigDecimal("0.05");
    private static final BigDecimal MAX_ORDER_LIMIT = new BigDecimal("10000.00");

    public enum CustomerTier {
        REGULAR,
        VIP,
        CORPORATE
    }

    public static class OrderRequest {
        private final String orderId;
        private final CustomerTier tier;
        private final BigDecimal subtotal;

        public OrderRequest(String orderId, CustomerTier tier, BigDecimal subtotal) {
            this.orderId = Objects.requireNonNull(orderId, "orderId cannot be null");
            this.tier = Objects.requireNonNull(tier, "CustomerTier cannot be null");
            this.subtotal = Objects.requireNonNull(subtotal, "subtotal cannot be null");
        }

        public String getOrderId() { return orderId; }
        public CustomerTier getTier() { return tier; }
        public BigDecimal getSubtotal() { return subtotal; }
    }

    public static class OrderSummary {
        private final String orderId;
        private final BigDecimal originalAmount;
        private final BigDecimal discountApplied;
        private final BigDecimal finalTotal;

        public OrderSummary(String orderId, BigDecimal originalAmount, BigDecimal discountApplied, BigDecimal finalTotal) {
            this.orderId = orderId;
            this.originalAmount = originalAmount;
            this.discountApplied = discountApplied;
            this.finalTotal = finalTotal;
        }

        public String getOrderId() { return orderId; }
        public BigDecimal getOriginalAmount() { return originalAmount; }
        public BigDecimal getDiscountApplied() { return discountApplied; }
        public BigDecimal getFinalTotal() { return finalTotal; }
    }

    public OrderSummary processOrder(OrderRequest request) {
        if (request.getSubtotal().compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Order subtotal must be strictly positive");
        }

        if (request.getSubtotal().compareTo(MAX_ORDER_LIMIT) > 0) {
            throw new IllegalStateException("Order exceeds maximum processing threshold of 10000.00");
        }

        BigDecimal discount = calculateDiscount(request.getTier(), request.getSubtotal());
        BigDecimal total = request.getSubtotal().subtract(discount).setScale(2, RoundingMode.HALF_UP);

        return new OrderSummary(
            request.getOrderId(),
            request.getSubtotal().setScale(2, RoundingMode.HALF_UP),
            discount.setScale(2, RoundingMode.HALF_UP),
            total
        );
    }

    private BigDecimal calculateDiscount(CustomerTier tier, BigDecimal subtotal) {
        switch (tier) {
            case VIP:
                return subtotal.multiply(VIP_DISCOUNT_RATE);
            case REGULAR:
                if (subtotal.compareTo(REGULAR_DISCOUNT_THRESHOLD) >= 0) {
                    return subtotal.multiply(REGULAR_DISCOUNT_RATE);
                }
                return BigDecimal.ZERO;
            case CORPORATE:
                return BigDecimal.ZERO;
            default:
                throw new UnsupportedOperationException("Unknown tier: " + tier);
        }
    }
}