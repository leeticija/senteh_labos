import csv
import math
import matplotlib.pyplot as plt

# Sensor names ordered:
sensor_names = ["Ni1000SOT","NTC","NTC-MAX6682","TERMOPAR-MAX6675","DS18B20","LM35DZ","TMP101NA"]

# List to store converted values from hex
decimal_values = []
# podaci spremljeni u obliku: {naziv_senzora1:[data1,data2...], naziv_senzora2:[data1,data2...]}
sensors_data_dict = {}

# Open the CSV file and read the hex data
for file_name in sensor_names:
    with open(file_name+".csv", mode='r') as file:
        csv_reader = csv.reader(file)
        # there's only one row in the CSV:
        for row in csv_reader:
            # Convert each hex value to decimal and add to data list
            # decimal_values = [int(value, 16) for value in row]
            decimal_values = [str(value) for value in row]
        sensors_data_dict[file_name] = decimal_values

def plot_data(dict):
    colors = ['red', 'green', 'blue', 'purple', 'orange', 'cyan', 'magenta']
    x_values = range(1, len(dict[sensor_names[0]]) + 1)
    plt.figure(figsize=(20, 8))  # Set the figure size
    # plottati sve senzore:
    for i, name in enumerate(sensor_names):
        plt.plot(x_values, dict[name], color=colors[i], label = name)
    # plt.plot(x_values, sensors_data_dict[sensor_names[1]], color='green', label=sensor_names[1])
    plt.xlabel('Sample indexes')
    plt.legend()
    plt.ylabel('Temperature')
    plt.title('Temperature Values From Data')
    plt.xticks(x_values)  # Label x-axis with index numbers
    plt.show()

def calculate_temp_NTC_max6682(hex_value):
    hex_value = hex_value[4:]
    binary_value = bin(int(hex_value, 16))[2:]
    relevant_bits = binary_value[:-5][-11:]
    decimal_value = int(relevant_bits, 2)
    temperature = decimal_value * 0.125
    return temperature

def calculate_temp_LM35DZ(hex_value):
    decimal_value = int(hex_value, 16)
    voltage = (decimal_value * 5000) / 1023
    temperature = voltage / 10
    return temperature-20

def calculate_temp_TMP101NA(hex_value):
    temp_value = int(hex_value[-4:], 16)
    temp_value >>= 4

    # Check if the number is negative (2's complement for 12-bit signed integer)
    if temp_value & (1 << 11):  # if the 12th bit is set
        temp_value -= 1 << 12  # apply two's complement

    # Each bit represents 0.0625°C
    temperature_celsius = temp_value * 0.0625
    return temperature_celsius

def calculate_temp_DS18B20(hex_value):
    temp_value = int(hex_value, 16)

    # Check if the temperature is negative by looking at the 15th bit (sign bit)
    if temp_value & (1 << 15):  # if bit 15 is set
        # Convert from two's complement (16-bit) for negative numbers
        temp_value -= 1 << 16

    temperature_celsius = temp_value # * 0.0625, senzor je vec mnozio s 0.0625 i iscitavao samo cjelobrojne
    return temperature_celsius

def calculate_temp_MAX6675(hex_value):
    raw_data = int(hex_value, 16)
    temperature_data = (raw_data >> 3) & 0x0FFF
    thermocouple_connected = (raw_data >> 2) & 1
    if thermocouple_connected != 0:
        return "Thermocouple not connected"
    temperature_celsius = temperature_data * 0.25
    return temperature_celsius

def calculate_temperature_NTC(hex_data, V_ref=3.3, B=4280, R1=16000, R2=25000, R3=10000, T1=298.15):
    """
    Calculate temperature from the ADC hex data of an NTC thermistor circuit.

    Parameters:
    - hex_data (str): Hexadecimal string representing the ADC reading.
    - V_ref (float): Reference voltage of the ADC. Default is 3.3 V.
    - B (float): Beta constant of the thermistor.
    - R_fixed (float): Fixed resistor in series with the thermistor, in ohms (16 kΩ).
    - R1 (float): Nominal resistance of the thermistor at T1 (10 kΩ at 25°C).
    - T1 (float): Reference temperature in Kelvin (298.15 K for 25°C).

    Returns:
    - float: Calculated temperature in Celsius.
    """

    # Step 1: Convert hex data to decimal
    adc_reading = int(hex_data, 16)

    # Step 2: Convert ADC reading to voltage
    V_adc = (adc_reading / 1023) * V_ref

    # Step 3: Calculate the thermistor resistance (R_thermistor) using the voltage divider
    if V_adc == 0:
        raise ZeroDivisionError("ADC voltage is zero, cannot calculate resistance.")
    R_parallel = R2 * ((V_ref / V_adc) - 1) # we calculate paralel based on the voltage and not resistance, 
                                            # because the voltage is chaning and affecting the resistance
    R_thermistor = (R1 * R_parallel) / (R1 - R_parallel)
    # Step 4: Use the temperature calculation formula
    ln_ratio = math.log(R_thermistor / R3)
    inv_T2 = (1 / T1) + (1 / B) * ln_ratio
    T2_kelvin = 1 / inv_T2
    T2_celsius = T2_kelvin - 273.15  # Convert from Kelvin to Celsius

    return T2_celsius

# Ni1000SOT:
# for i in range(len(sensors_data_dict["Ni1000SOT"])):
#     data1 = sensors_data_dict["Ni1000SOT"][i]
#     Uni = (int(data1, 16)/1023)*5 # izlazni napon iz RTD senzora
#     R1 = 2967
#     R2 = 10000
#     R3 = 3008
#     R4 = 14880
#     denominator = 1+(R4/R2)+(R4/R3)
#     numerator = (Uni/5)+(R4/R2)
#     Rp = numerator/denominator
#     Rni = (Rp*R1)/(1-Rp)
#     # print("Otpor Rni:", Rni)
#     # temperature = (Rni/1000-1)/0.006178
#     print(data1)
#     temperature = -412.6 + (140.41 * math.sqrt((1+0.00764*Rni))) - (6.25*pow(10, -17) * pow(Rni,5)) - (1.25*pow(10,-24)*pow(Rni, 7))
#     # temperature = (Rni-1000)/61.78
#     # print(temperature)

## Ni10000SOT##
def calculate_temperature_Ni1000SOT(hex_value):
    # Convert hex to voltage (0-5V range based on 10-bit ADC)
    Uni = (int(hex_value, 16) / 1023) * 5  # izlazni napon iz RTD senzora
    # Circuit resistor values
    R1 = 2967
    R2 = 10000
    R3 = 3800
    R4 = 14880
    denominator = 1 + (R4 / R2) + (R4 / R3)
    numerator = (Uni / 5) + (R4 / R2)
    Rp = numerator / denominator
    Rni = (Rp * R1) / (1 - Rp)
    temperature = (Rni - 1000) / 6.178 - 20
    return temperature

def convert_all_data():
    convert_data_all = {}
    convert_data_all["Ni1000SOT"] = [round(calculate_temperature_Ni1000SOT(x),2) for x in sensors_data_dict["Ni1000SOT"]]
    convert_data_all["NTC"] = [round(calculate_temperature_NTC(x),2) for x in sensors_data_dict["NTC"]]
    convert_data_all["NTC-MAX6682"] = [round(calculate_temp_NTC_max6682(x),2) for x in sensors_data_dict["NTC-MAX6682"]]
    convert_data_all["TERMOPAR-MAX6675"] = [round(calculate_temp_MAX6675(x),2) for x in sensors_data_dict["TERMOPAR-MAX6675"]]
    convert_data_all["DS18B20"] = [round(calculate_temp_DS18B20(x),2) for x in sensors_data_dict["DS18B20"]]
    convert_data_all["LM35DZ"] = [round(calculate_temp_LM35DZ(x),2) for x in sensors_data_dict["LM35DZ"]]
    convert_data_all["TMP101NA"] = [round(calculate_temp_TMP101NA(x),2) for x in sensors_data_dict["TMP101NA"]]
    return convert_data_all

def print_table(dict):
    column_width = 15
    num_columns = 8
    print()
    print("-" * (column_width * num_columns))
    # headers = [f"{sensor_name}" for sensor_name in ["", sensor_names]]
    print("".join(header.center(column_width) for header in [""]+sensor_names))
    for percentage in [0.2, 0.4, 0.6, 0.8]:
        print("-" * (column_width * num_columns))
        redak = [str(percentage*100)+"%"]
        for sensor in sensor_names:
            index = int(len(dict[sensor])*percentage)
            redak.append(dict[sensor][index])
        print("".join(str(value).center(column_width) for value in redak))
    print("-" * (column_width * num_columns))
    print()

# call data conversion for all sensors:

# 1.a)
converted_data = convert_all_data()
print("Tablica 1.a)")
print_table(converted_data)
plot_data(converted_data)


# 2.a)
new_sensor_data_dict = {}
for name in sensor_names:
    data = converted_data[name]
    averages = []
    chunk_size = 10
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]  # Get a chunk of 10 elements
        average = sum(chunk) / len(chunk)  # Calculate the average of the chunk
        averages.append(round(average,2))  # Append the average to the new list
    new_sensor_data_dict[name] = averages

plot_data(new_sensor_data_dict)
print("Tablica 2.a)")
print_table(new_sensor_data_dict)

# 3.a)
new_sensor_data_dict = {}
for name in sensor_names:
    data = converted_data[name]
    averages = []
    chunk_size = 10
    for i in range(0, len(data)-10, 1):
        chunk = data[i:i + chunk_size]  # Get a chunk of 10 elements
        average = sum(chunk) / len(chunk)  # Calculate the average of the chunk
        averages.append(round(average,2))  # Append the average to the new list
    new_sensor_data_dict[name] = averages
print("3.a)")
print_table(new_sensor_data_dict)
