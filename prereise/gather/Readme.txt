Data Download would cost over 1 hour. If don’t want to wait. The downloaded data is already in target folder. If just want to test, please start at Step3.

Step1: Get hiflddata:

1.Enter the workspace "\HIFLD_Profile_APP"

2.Run command "python data_trans.py".

3.Run command "python plant_agg.py".

4.Copy the documents in “output”, paste in “powersimdata/network/usa_tamu/data” manually. If it is the first time to run project，also copy the zone.csv in “hiflddata/data” folder to “powersimdata/network/usa_tamu/data”.


Step2: Download HIFLD profile:

1.Enter the environment of PreReise.

2.Run winddata.py, solardata_nsrdb_sam.py, hydrodata.py

3.Move the output(wind.csv, solar.csv, hydro.csv) to folder “\HIFLD_Profile_APP\output\PreReise_HIFLD_Profiles_Raw”

(Data Download would cost over 1 hour. If don’t want to wait. The downloaded data is already in target folder.)


Step3: Get wind\solar\hydro data:

1.Enter the workspace "\HIFLD_Profile_APP"

2.Run command "python src\wind_plant_cross_validation.py" to transfer the wind data. The output will be in folder "output\HIFLD_Profiles_Final".

3.Run command "python src\solar_plant_cross_validation.py" to transfer the solar data. The output will be in folder "output\HIFLD_Profiles_Final".

4.Run command "python src\hydro_plant_cross_validation.py" to transfer the hydro data. The output will be in folder "output\HIFLD_Profiles_Final".

5(optional. If need Eastern\Western\Texas data). 
Run command "python src\tamu_data_devide.py". The output will be in folder "output\HIFLD_Profiles_Final\Texas(Eastern,Western)"


Step4:Get demand data:

1.Enter the workspace "\HIFLD_Profile_APP\Demand"

2.Run command "python demand_trans.py". The output will be in folder "demand_output".

3(optional. If need Eastern\Western\Texas data). 
Run command "python src\tamu_data_devide.py". The output will be in folder "demand_output\Texas(Eastern,Western)".