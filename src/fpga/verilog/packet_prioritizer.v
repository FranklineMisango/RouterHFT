"""
FPGA packet prioritization module for hardware-accelerated market data processing.
Implements low-latency packet classification and forwarding.
"""

// Packet Prioritization Engine
// Classifies incoming packets based on exchange-specific criteria
module packet_prioritizer #(
    parameter DATA_WIDTH = 512,
    parameter ADDR_WIDTH = 64,
    parameter NUM_EXCHANGES = 8,
    parameter PRIORITY_LEVELS = 4
)(
    input wire clk,
    input wire rst_n,
    
    // Input packet interface
    input wire [DATA_WIDTH-1:0] pkt_data_in,
    input wire pkt_valid_in,
    input wire pkt_sop_in,
    input wire pkt_eop_in,
    output wire pkt_ready_out,
    
    // Output packet interface
    output reg [DATA_WIDTH-1:0] pkt_data_out,
    output reg pkt_valid_out,
    output reg pkt_sop_out,
    output reg pkt_eop_out,
    output reg [PRIORITY_LEVELS-1:0] pkt_priority_out,
    input wire pkt_ready_in,
    
    // Configuration interface
    input wire [31:0] config_addr,
    input wire [31:0] config_data,
    input wire config_write,
    
    // Statistics interface
    output reg [63:0] packets_processed,
    output reg [63:0] high_priority_packets,
    output reg [63:0] timestamp_ns
);

// Internal signals
reg [DATA_WIDTH-1:0] pkt_buffer [0:15];
reg [3:0] buffer_write_ptr;
reg [3:0] buffer_read_ptr;
reg buffer_full;
reg buffer_empty;

// Packet classification logic
reg [15:0] eth_type;
reg [31:0] src_ip;
reg [31:0] dst_ip;
reg [15:0] src_port;
reg [15:0] dst_port;
reg [7:0] protocol;

// Exchange classification table
reg [31:0] exchange_ip_table [0:NUM_EXCHANGES-1];
reg [15:0] exchange_port_table [0:NUM_EXCHANGES-1];
reg [PRIORITY_LEVELS-1:0] exchange_priority_table [0:NUM_EXCHANGES-1];

// Timestamp counter (nanosecond precision)
reg [63:0] timestamp_counter;

// State machine for packet processing
typedef enum reg [2:0] {
    IDLE,
    PARSE_HEADER,
    CLASSIFY,
    OUTPUT,
    WAIT_READY
} state_t;

state_t current_state, next_state;

// Clock domain crossing for high-frequency timestamp
always_ff @(posedge clk) begin
    if (!rst_n) begin
        timestamp_counter <= 64'h0;
    end else begin
        timestamp_counter <= timestamp_counter + 1;
    end
end

// Packet buffer management
always_ff @(posedge clk) begin
    if (!rst_n) begin
        buffer_write_ptr <= 4'h0;
        buffer_read_ptr <= 4'h0;
        buffer_full <= 1'b0;
        buffer_empty <= 1'b1;
    end else begin
        // Buffer write logic
        if (pkt_valid_in && pkt_ready_out && !buffer_full) begin
            pkt_buffer[buffer_write_ptr] <= pkt_data_in;
            buffer_write_ptr <= buffer_write_ptr + 1;
        end
        
        // Buffer read logic
        if (pkt_ready_in && pkt_valid_out && !buffer_empty) begin
            buffer_read_ptr <= buffer_read_ptr + 1;
        end
        
        // Buffer status update
        buffer_full <= (buffer_write_ptr + 1) == buffer_read_ptr;
        buffer_empty <= buffer_write_ptr == buffer_read_ptr;
    end
end

assign pkt_ready_out = !buffer_full;

// Packet header parsing
always_ff @(posedge clk) begin
    if (!rst_n) begin
        eth_type <= 16'h0;
        src_ip <= 32'h0;
        dst_ip <= 32'h0;
        src_port <= 16'h0;
        dst_port <= 16'h0;
        protocol <= 8'h0;
    end else if (current_state == PARSE_HEADER && pkt_valid_in) begin
        // Extract Ethernet type (assuming standard Ethernet frame)
        eth_type <= pkt_data_in[111:96];
        
        // Extract IP header fields (IPv4)
        if (eth_type == 16'h0800) begin
            protocol <= pkt_data_in[71:64];
            src_ip <= pkt_data_in[159:128];
            dst_ip <= pkt_data_in[127:96];
            
            // Extract TCP/UDP ports
            if (protocol == 8'h06 || protocol == 8'h11) begin
                src_port <= pkt_data_in[207:192];
                dst_port <= pkt_data_in[191:176];
            end
        end
    end
end

// Packet classification engine
reg [PRIORITY_LEVELS-1:0] classified_priority;
reg classification_valid;

always_comb begin
    classified_priority = 4'h0;  // Default lowest priority
    classification_valid = 1'b0;
    
    // Check against exchange IP/port tables
    for (int i = 0; i < NUM_EXCHANGES; i++) begin
        if ((dst_ip == exchange_ip_table[i] || src_ip == exchange_ip_table[i]) &&
            (dst_port == exchange_port_table[i] || src_port == exchange_port_table[i])) begin
            classified_priority = exchange_priority_table[i];
            classification_valid = 1'b1;
            break;
        end
    end
    
    // Special handling for market data protocols
    case (dst_port)
        16'd1234: classified_priority = 4'hF;  // Critical market data
        16'd5678: classified_priority = 4'hE;  // Order entry
        16'd9012: classified_priority = 4'hD;  // Market status
        default: begin
            if (!classification_valid) begin
                classified_priority = 4'h1;  // Default priority
            end
        end
    endcase
end

// Main state machine
always_ff @(posedge clk) begin
    if (!rst_n) begin
        current_state <= IDLE;
    end else begin
        current_state <= next_state;
    end
end

always_comb begin
    next_state = current_state;
    
    case (current_state)
        IDLE: begin
            if (pkt_valid_in && pkt_sop_in) begin
                next_state = PARSE_HEADER;
            end
        end
        
        PARSE_HEADER: begin
            if (pkt_valid_in) begin
                next_state = CLASSIFY;
            end
        end
        
        CLASSIFY: begin
            if (classification_valid) begin
                next_state = OUTPUT;
            end
        end
        
        OUTPUT: begin
            if (pkt_ready_in) begin
                if (pkt_eop_out) begin
                    next_state = IDLE;
                end else begin
                    next_state = WAIT_READY;
                end
            end
        end
        
        WAIT_READY: begin
            if (pkt_ready_in && pkt_eop_out) begin
                next_state = IDLE;
            end
        end
        
        default: next_state = IDLE;
    endcase
end

// Output generation
always_ff @(posedge clk) begin
    if (!rst_n) begin
        pkt_data_out <= {DATA_WIDTH{1'b0}};
        pkt_valid_out <= 1'b0;
        pkt_sop_out <= 1'b0;
        pkt_eop_out <= 1'b0;
        pkt_priority_out <= 4'h0;
    end else begin
        case (current_state)
            OUTPUT, WAIT_READY: begin
                if (!buffer_empty && pkt_ready_in) begin
                    pkt_data_out <= pkt_buffer[buffer_read_ptr];
                    pkt_valid_out <= 1'b1;
                    pkt_sop_out <= (buffer_read_ptr == 0);
                    pkt_eop_out <= (buffer_read_ptr == buffer_write_ptr - 1);
                    pkt_priority_out <= classified_priority;
                end else begin
                    pkt_valid_out <= 1'b0;
                end
            end
            
            default: begin
                pkt_valid_out <= 1'b0;
                pkt_sop_out <= 1'b0;
                pkt_eop_out <= 1'b0;
            end
        endcase
    end
end

// Configuration interface
always_ff @(posedge clk) begin
    if (!rst_n) begin
        // Initialize exchange tables with default values
        for (int i = 0; i < NUM_EXCHANGES; i++) begin
            exchange_ip_table[i] <= 32'h0;
            exchange_port_table[i] <= 16'h0;
            exchange_priority_table[i] <= 4'h1;
        end
    end else if (config_write) begin
        case (config_addr[7:0])
            8'h00: exchange_ip_table[config_addr[11:8]] <= config_data;
            8'h10: exchange_port_table[config_addr[11:8]] <= config_data[15:0];
            8'h20: exchange_priority_table[config_addr[11:8]] <= config_data[PRIORITY_LEVELS-1:0];
            default: ; // Invalid address
        endcase
    end
end

// Statistics collection
always_ff @(posedge clk) begin
    if (!rst_n) begin
        packets_processed <= 64'h0;
        high_priority_packets <= 64'h0;
        timestamp_ns <= 64'h0;
    end else begin
        timestamp_ns <= timestamp_counter;
        
        if (pkt_valid_out && pkt_ready_in && pkt_eop_out) begin
            packets_processed <= packets_processed + 1;
            
            if (pkt_priority_out >= 4'hC) begin
                high_priority_packets <= high_priority_packets + 1;
            end
        end
    end
end

endmodule

// PCIe DMA bypass module for ultra-low latency
module pcie_dma_bypass #(
    parameter DATA_WIDTH = 512,
    parameter ADDR_WIDTH = 64
)(
    input wire clk,
    input wire rst_n,
    
    // PCIe interface
    input wire [DATA_WIDTH-1:0] pcie_data_in,
    input wire pcie_valid_in,
    input wire pcie_sop_in,
    input wire pcie_eop_in,
    output wire pcie_ready_out,
    
    // Direct memory interface (bypassing DMA)
    output reg [DATA_WIDTH-1:0] mem_data_out,
    output reg [ADDR_WIDTH-1:0] mem_addr_out,
    output reg mem_write_en,
    output reg mem_read_en,
    input wire [DATA_WIDTH-1:0] mem_data_in,
    input wire mem_ready,
    
    // Packet output interface
    output reg [DATA_WIDTH-1:0] pkt_data_out,
    output reg pkt_valid_out,
    output reg pkt_sop_out,
    output reg pkt_eop_out,
    input wire pkt_ready_in
);

// Direct packet forwarding for lowest latency
always_ff @(posedge clk) begin
    if (!rst_n) begin
        pkt_data_out <= {DATA_WIDTH{1'b0}};
        pkt_valid_out <= 1'b0;
        pkt_sop_out <= 1'b0;
        pkt_eop_out <= 1'b0;
    end else begin
        // Direct bypass - minimal latency path
        pkt_data_out <= pcie_data_in;
        pkt_valid_out <= pcie_valid_in;
        pkt_sop_out <= pcie_sop_in;
        pkt_eop_out <= pcie_eop_in;
    end
end

assign pcie_ready_out = pkt_ready_in;

// Memory interface for configuration and statistics
always_ff @(posedge clk) begin
    if (!rst_n) begin
        mem_data_out <= {DATA_WIDTH{1'b0}};
        mem_addr_out <= {ADDR_WIDTH{1'b0}};
        mem_write_en <= 1'b0;
        mem_read_en <= 1'b0;
    end else begin
        // Memory operations handled separately
        // to avoid interfering with packet forwarding
        mem_write_en <= 1'b0;
        mem_read_en <= 1'b0;
    end
end

endmodule
