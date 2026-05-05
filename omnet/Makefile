# Makefile for OMNeT++ HFT NIC simulation
# Generate with: opp_makemake -f --deep

include $(OMNETPP_CONFIGFILE)

# msgc:=$(MSGC) --msg6 -I$(OMNETPP_INCL_DIR)
# MSGCOPTS?=$(MSGCOPTS) -I$(OMNETPP_INCL_DIR)
# CCFLAGS?=$(CCFLAGS) -I$(OMNETPP_INCL_DIR)
# NEDPATH?=$(NEDPATH):$(OMNETPP_NEDPATH)

COPTS?=$(COPTS_RELEASE)
CFLAGS?=$(CFLAGS) -std=c++11

OBJS=ProgrammableNIC.o CongestionControl.o TrafficGenerator.o PacketSink.o

NEDS=HFT_NIC_Network.ned

TARGET=HFT_NIC_Network$(EXE_SUFFIX)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS) Makefile
	$(CXX) $(LDFLAGS) -o $@ $(OBJS) $(AS_NEEDED_OFF) $(WHOLE_ARCHIVE_ON) -loppenvir -loppmain -loppcmdenv -loppsim -loppcommon $(WHOLE_ARCHIVE_OFF) $(OMNETPP_LIB_DIR) -Wl,-rpath,$(OMNETPP_LIB_DIR)

%.o: %.cc $(NEDSOURCES) Makefile
	$(CXX) -c $(CXXFLAGS) $(COPTS) -o $@ $<

clean:
	$(RM) $(OBJS) $(TARGET)

depend:
	$(MAKEDEPEND) $(INCLUDE) -f$(MAKEFILE) -- $(CC) -MM $(CXXFLAGS) $(COPTS) -- $(SOURCES)
