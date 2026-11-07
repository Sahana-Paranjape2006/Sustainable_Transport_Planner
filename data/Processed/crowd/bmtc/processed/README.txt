BMTC / CMP passenger-demand extraction package
Source file: Bengaluru_CMP_2019_Draft.pdf (uploaded in this conversation)
Inspection: entire 226-page PDF; relevant CMP printed pages 2-39 to 2-42.

FILES
- bmtc_terminal_passenger_demand.csv: Table 2-23, 16 terminal/facility rows, daily inflow/outflow and peak-hour arrival/departure.
- cmp_bus_stop_trip_purpose_distribution.csv: Table 2-22, percentages for trip purpose from 472-stop, 16-hour bus-stop passenger survey.
- cmp_terminal_passenger_dispersal.csv: Table 2-24, passenger dispersal mode distribution.
- cmp_terminal_access_travel_time.csv: Table 2-25, travel time to reach bus terminals.
- cmp_terminal_travel_frequency.csv: Table 2-26, travel frequency distribution.
- cmp_extraction_and_data_dictionary.xlsx: all extracted tables and limitations/provenance.

IMPORTANT DATA LIMITATIONS
The report describes boarding/alighting counts at 472 bus stops during a 16-hour survey, but the CMP pages inspected do not publish the underlying stop-wise or route-wise numerical boarding/alighting records. The report's Table 2-23 is aggregate terminal/facility inflow/outflow and peak-hour arrival/departure, not bus-level occupancy.
Tables 2-22 to 2-26 cite RITES Phase III Corridors of Bangalore Metro, 2016. Treat these as historical survey summaries.
No synthetic records or invented passenger counts have been added.
The extracted tables alone are not enough to train a reliable route-stop-hour occupancy prediction model.
