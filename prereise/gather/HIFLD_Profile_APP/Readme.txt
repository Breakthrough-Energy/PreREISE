Get wind\solar\hydro data:

1.Enter the workspace "\HIFLD_Profile_APP"

2.Run command "python src\wind_plant_cross_validation.py" to transfer the wind data. The output will be in folder "output\HIFLD_Profiles_Final".

3.Run command "python src\solar_plant_cross_validation.py" to transfer the wind data. The output will be in folder "output\HIFLD_Profiles_Final".

4.Run command "python src\hydro_plant_cross_validation.py" to transfer the wind data. The output will be in folder "output\HIFLD_Profiles_Final".

5(optional). If you need Eastern\Western\Texas data， run command "python src\tamu_data_devide.py". The output will be in folder "output\HIFLD_Profiles_Final\Texas(Eastern,Western)"




Get demand data:

1.Enter the workspace "\HIFLD_Profile_APP\Demand"

2.Run command "python demand_trans.py". The output will be in folder "demand_output".

3(optional). If you need Eastern\Western\Texas data，run command "python src\tamu_data_devide.py". The output will be in folder "output\HIFLD_Profiles_Final\Texas(Eastern,Western)".