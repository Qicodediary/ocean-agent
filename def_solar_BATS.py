
import numpy as np
import math as mt
import calendar


def year_days(year):
    if calendar.isleap(year):
        return 366
    else:
        return 365


def surface_clear_sky_solar_v1(parameters_surf):
# This model requires the location, time span, initial conditions which includes the forcing (mixed layer depth), and the parameters
#at the surface layer and subsurface layer
    #===========================================================================================
    #Unpack parameters and define parameters to calculate
    #===========================================================================================
    
    # 1. Unpack initial conditions


    # 2. Unpack parameters
    Lat, year, SolarK, AtmAtt = parameters_surf

    # 3. define parameters used in C:CHl model 
        

    
    
    #check how many years
    NN=len(year)
    #define initial zero value to calculate the total days (time step) of this simulation
    LL = 0
    for n in range(NN):
        LL += year_days(year[n])
    
    # Initialize arrays 
    I_clear= np.full(LL, np.nan)
    output_D1= np.full(LL, np.nan)
    output_W1 = np.full(LL, np.nan)




    # Loop through each year of year
    Day = -1
    for Yr in range(NN):
        y_day             =  year_days(year[Yr])   
        for i in range(y_day):
            
            Day           += 1
            #=================================================================================
  
            # Compute surface PAR at latitude for times of day and dawn to noon and production rate integration down to MLD
            D1            = 23.45*mt.sin(mt.radians((360.*(284.+i+1)/365.)))        # Decination = angle of the sun above the equator on each day
            output_D1[Day]= D1
            
            W1            = mt.degrees(mt.acos(-1.*(mt.tan(mt.radians(Lat)) * mt.tan(mt.radians(D1)))))  # Angle(deg) between south (i.e. noon) and setting sun
            output_W1[Day]=W1
            
            #========================================================================================
            # One-half daylength, in hours
            L1            = W1/15.  # Earth rotates 15 = degrees / hour =360/24 
            
            Rx            = 1./mt.sqrt(1.+0.033*np.cos(np.deg2rad((360.*(i+1)/365.)))) # Distance of Earth from sun relative to average, a minor effect
            
            VtofD         = L1/40.
            TofD          = 12.01-L1-VtofD   #T of the Day
          
            # Set initial values for growth rate and light at surface and subsurface layers for each day
            cn_sgr_sub    = 40 #time step used to calulate daily light


            Io_t = 0    
            # Loop over dawn to noon in 40 steps in each day
            for j in range(cn_sgr_sub):
                TofD      =  TofD + VtofD   # for the following see Brock (1981)
                W2        =  (TofD-12.)*15.
                CosZen    = np.sin(np.deg2rad(D1))*np.sin(np.deg2rad(Lat)) \
                          +np.cos(np.deg2rad(D1))*np.cos(np.deg2rad(Lat)) \
                          *np.cos(np.deg2rad(W2))
                Isurf     = SolarK*CosZen/(Rx*Rx) 
                Io        = Isurf
                Io_t = Io_t + Io
 
                #================================================================================
               
            #Out of loop 40: 
            #================================================================================
            #                   light method 1
            #=================================================================================   
            
            DL = 2*L1*60*60 #Seconds 
            #DL=daylen[Day]
            DL_24 = 86400 #seconds
            Io_t_inital = 2*Io_t * (DL/80)
            I_clear[Day]= Io_t_inital / DL_24

            
       
            


    return I_clear



            
            
            
            
def two_layered_model_stocks_interaction_change_light(Lat, year, initial_conditions, parameters_surf, parameters_sub,AtmAtt,frac_cs):
# This model requires the location, time span, initial conditions which includes the forcing (mixed layer depth), and the parameters
#at the surface layer and subsurface layer
    #===========================================================================================
    #Unpack parameters and define parameters to calculate
    #===========================================================================================
    
    # 1. Unpack initial conditions
    P, Nut, Z, Mprev, MLZ, P_sub, Z_sub, M_EU, Chla, Chla_sub = initial_conditions

    # 2. Unpack parameters
    SolarK, ParFrac, Kdw, Kdp, Vmax, alpha, Ks, Nd, m, Gamma, CN, frac, mup, mug, muz, a,k_e, theta_m = parameters_surf
    alpha_sub, Kdp_sub, Vmax_sub, a_sub, k_e_sub, Gamma_sub, m_sub, CN_sub, X_sub = parameters_sub
    
    # 3. define parameters used in C:CHl model 
        
    C_to_N       = 106/16    # C:N ratio 106:16
    mgC_to_mmolC = 12        # 1mmolC = 12mgC
    #theta_m      = 0.01      # define theta_m for C:CHl ratio calculation
   # X_sub        = 158       # half of time-mean surface X_ratio 
    
    
    #check how many years
    NN=len(year)
    #define initial zero value to calculate the total days (time step) of this simulation
    LL = 0
    for n in range(NN):
        LL += year_days(year[n])
    
    # Initialize arrays 
    Pstr, Nutstr, Zstr, I, Depth_EU, I_sub, Pstr_sub, Nd_str, Zstr_sub, Chla_str, Chla_sub_str, X_ratio= [np.full(LL, np.nan) for _ in range(12)]



    # Loop through each year of year
    Day = -1
    for Yr in range(NN):
        y_day             =  year_days(year[Yr])
        # Loop through the days
        for i in range(y_day):
            Day           += 1
            #=================================================================================
            #
            #                    COMPUTE THE LIGHT ENVIRONMENT
            #
            #=================================================================================
            Kd            = Kdw + Kdp * Chla         # calculate the total light attenuation at the surface layer 
            Depth_EU[Day] = 13.8/Kd                  #calculate euphotic zone

            Kd_sub     = Kdw    + Kdp_sub * Chla_sub # calculate the total light attenuation at the subsurface layer 

            # Compute surface PAR at latitude for times of day and dawn to noon and production rate integration down to MLD
            D1            = 23.45*mt.sin(mt.radians((360.*(284.+i+1)/365.)))                             # Decination = angle of the sun above the equator on each day
            W1            = mt.degrees(mt.acos(-1.*(mt.tan(mt.radians(Lat)) * mt.tan(mt.radians(D1)))))  # Angle(deg) between south (i.e. noon) and setting sun
            
            
            #========================================================================================
            # One-half daylength, hours to noon
            L1            = W1/15.  # Earth rotates 15 = degrees / hour =360/24
            Rx            = 1./mt.sqrt(1.+0.033*np.cos(np.deg2rad((360.*(i+1)/365.)))) # Distance of Earth from sun relative to average, a minor effect
            VtofD         = L1/40.
            TofD          = 12.01-L1-VtofD
          
            # Set initial values for growth rate and light at surface and subsurface layers for each day
            SGr           = 0  #surface growth rate initial value
            SGr_sub       = 0  #subsurface growth rate initial value
            I_d2n         = 0  #surface light initial value
            I_d2n_sub     = 0  #subsurface light initial value 
            cn_sgr_sub    = 40 #time step used to calulate daily light


            
            # Loop over dawn to noon in 40 steps in each day
            for j in range(cn_sgr_sub):
                TofD      =  TofD + VtofD   # for the following see Brock (1981)
                W2        =  (TofD-12.)*15.
                CosZen    = np.sin(np.deg2rad(D1))*np.sin(np.deg2rad(Lat)) \
                          +np.cos(np.deg2rad(D1))*np.cos(np.deg2rad(Lat)) \
                          *np.cos(np.deg2rad(W2))
                Isurf     = SolarK*CosZen/(Rx*Rx)
                Io        = Isurf*AtmAtt[Day]*ParFrac *frac_cs[Day]
                #================================================================================
                #
                #                    Surface layer 
                #
                #=================================================================================
                sm        = 0 #surface layer light initial at each time step of 40 steps
                for k in range(1,int(MLZ[Day])+1):
                    Iz    = Io*np.exp(-1.*Kd*k) #calculate light
                    sm    = sm+Iz #accumulated from surface to MLZ
                    Gr    = (1. - mt.exp(-alpha*Iz/Vmax)) #COMPUTE Phytoplankton Growth Rate for each step from 0 to MLZ and dawn to non             
                    SGr   += Gr #sum the growth rate
                I_d2n     = I_d2n + sm/MLZ[Day] # calculate MLD-averaged irradiance from dawn to noon
                #=================================================================================
                #
                #                   Subsurface layer
                #
                #=================================================================================

                sm_sub       = 0 #subsurface layer initial at each time step of 40 steps
                I_m          = Io*np.exp(-1.*Kd*int(MLZ[Day]))  #light at MLD depth 
                for k2 in range(int(MLZ[Day])+1, int(Depth_EU[Day])+1):
                    Iz2      = I_m*np.exp(-1.*Kd_sub*k2) #subsurface light attenuates from MLD light
                    sm_sub   = sm_sub+Iz2 #accumulated the light from MLD to the euphotic zone
                    Gr_sub   = (1. - mt.exp(-alpha_sub*Iz2/Vmax_sub)) #calculate growth rate
                    SGr_sub  += Gr_sub # sum the growth rate
                I_d2n_sub    = I_d2n_sub+sm_sub/(Depth_EU[Day]-MLZ[Day]) # calculate vertical-averaged irradiance from dawn to noon

            #Out of loop 40: 
            #================================================================================
            #                    Surface layer : averaged light
            #=================================================================================   
        
            I[Day]=2*I_d2n/cn_sgr_sub              # *2 to get dawn to dusk for surface layer light, divided by total time step (40) to get the averaged value

            #=================================================================================
            #                    Subsurface layer : averaged light
            #=================================================================================

            I_sub[Day]=2*I_d2n_sub/cn_sgr_sub      # *2 to get dawn to dusk for subsurface layer light, divided by total time step (40) to get the averaged value
       
            #================================================================================
            #
            #                    Surface layer: growth rate
            #
            #=================================================================================
            # Calculate Phytoplankton Growth Rate over the day (LIGHT EFFECT)
            AveGr      = 2.*Vmax*SGr/(MLZ[Day]*cn_sgr_sub)  # (2* to get dawn to dusk) (divided by MLD and total time steps of 40 to get averaged values)
            # Calculate Phytoplankton Growth rate (NUTRIENT EFFECT)
            NL         = Vmax*Nut/(Ks+Nut)
            # Take the minimum growth rate between light and nutrient growth rate
            G          = min(NL, AveGr)

            #================================================================================
            #
            #                    Subsurface layer: growth rate 
            #
            #=================================================================================  
            # This layer must be limited by light so only calculate the light growth rate
            G_sub= 2.*Vmax_sub*SGr_sub/((Depth_EU[Day]-MLZ[Day]) *cn_sgr_sub)  # (2* to get dawn to dusk) (divided by (euphotic zone-MLD) and total time steps of 40 to get averaged values)    
                
            
            #================================================================================
            #
            #                    Surface layer: zooplankton grazing
            #
            #=================================================================================  
            graz       = a*k_e*(P**2)/(a+k_e*(P**2))
         
            #================================================================================
            #
            #                    Subsurface layer: zooplankton grazing
            #
            #=================================================================================  
            graz_sub   = a_sub*k_e_sub*(P_sub**2)/(a_sub+k_e_sub*(P_sub**2))

            # Calculate MLD entrainment effect on nutrient exchange 
            zeta_deep       = MLZ[Day] - Mprev if MLZ[Day] > Mprev else 0.
            zeta_shallow    = MLZ[Day] - Mprev if MLZ[Day] < Mprev else 0.
            
            #zeta_shallow  =  Mprev - MLZ[Day] if  MLZ[Day] < Mprev else 0.  #zeta and zeta_shallow are always positive 
            #================================================================================
            #
            #                    Surface layer core function 
            #
            #=================================================================================   
            #calculate changes in phytoplankton, nutrient and zooplankton concentrations at surface layer
            
            DP         = G * P - m*P - graz*Z - (MLZ[Day] - Mprev)*P/MLZ[Day] +zeta_shallow*P/MLZ[Day]
            DN         = - G * P + mup*m*P + (1-Gamma-mug) * graz * Z + muz*(CN*(Z**2)) + (frac*MLZ[Day])*(Nd- Nut)/MLZ[Day]- (MLZ[Day] - Mprev)*Nut/MLZ[Day] + zeta_deep*P_sub/MLZ[Day] + zeta_deep*Nd/MLZ[Day] + zeta_shallow*Nut/MLZ[Day]
            DZ         = graz * Gamma * Z - CN*(Z**2)- (MLZ[Day] - Mprev)*Z/MLZ[Day]
           
            
            #================================================================================
            #
            #                    Subsurface layer core function
            #
            #================================================================================= 
            #calculate changes in phytoplankton, nutrient and zooplankton concentrations at the subsurface layer

            DP_sub     = G_sub * P_sub - m_sub * P_sub - graz_sub * Z_sub -((Depth_EU[Day]-MLZ[Day])-(M_EU-Mprev))*P_sub/(Depth_EU[Day]-MLZ[Day]) - zeta_deep*P_sub/(Depth_EU[Day]-MLZ[Day])
            DN_sub     = - G_sub * P_sub +  m_sub * P_sub + (1-Gamma_sub) * graz_sub*Z_sub +CN_sub*(Z_sub**2) -((Depth_EU[Day]-MLZ[Day])-(M_EU-Mprev))*Nd/(Depth_EU[Day]-MLZ[Day])  - zeta_shallow*P/(Depth_EU[Day]-MLZ[Day]) - zeta_deep*Nd/(Depth_EU[Day]-MLZ[Day]) - zeta_shallow*Nut/(Depth_EU[Day]-MLZ[Day])
            DZ_sub     = graz_sub * Gamma_sub * Z_sub - CN_sub*(Z_sub**2) - ((Depth_EU[Day]-MLZ[Day])-(M_EU-Mprev))*Z_sub/(Depth_EU[Day]-MLZ[Day])
            
            #================================================================================= 
            #                  calcualte subsurface state variables
            #================================================================================= 
            P_sub      = P_sub + DP_sub 
            Z_sub      = Z_sub + DZ_sub 
            Nd         = Nd - (frac*MLZ[Day])*(Nd- Nut)/(Depth_EU[Day]-MLZ[Day])+ (1-muz)*CN*(Z**2)*MLZ[Day]/(Depth_EU[Day]-MLZ[Day]) +mug*graz*Z*MLZ[Day]/(Depth_EU[Day]-MLZ[Day]) + (1-mup)*m*P*MLZ[Day]/(Depth_EU[Day]-MLZ[Day]) + DN_sub
 
            
            #================================================================================= 
            #                  calcualte surface state variables
            #================================================================================= 
            P          = P   + DP
            Nut        = Nut + DN
            Z          = Z   + DZ
    

            #================================================================
            #                  calculate surface chla
            #================================================================
            Ik            = Vmax/alpha
            I_star        = I[Day]/Ik
            X             = I_star/(theta_m*(1-np.exp(-I_star)))
            X_ratio[Day]  = X                                  #caluclate C:Chl ratio 
            Chla          = P*(C_to_N)*(1/X)*mgC_to_mmolC      #convert P to chla in mg/m^3

            
            
            #================================================================
            #                  calculate subsurface chla
            #================================================================
            Chla_sub     = P_sub*(C_to_N)*(1/X_sub)*mgC_to_mmolC  #X_sub=158 is half of time-mean surface X_ratio 

            #=================================================================================
            #                   Save state variables into timeseries
            #=================================================================================
            #calcualte the thickness of the subsurface layer 
            zD           = Depth_EU[Day]-MLZ[Day] 
            
            #calcualte stocks: averaged concentration multiplied by the thickness of each layer
            Pstr[Day],      Nutstr[Day],   Zstr[Day],   Chla_str[Day]        = P*MLZ[Day], Nut*MLZ[Day], Z*MLZ[Day],  Chla*MLZ[Day]
            Pstr_sub[Day],  Zstr_sub[Day], Nd_str[Day], Chla_sub_str[Day]    = P_sub*zD,   Z_sub*zD,     Nd*zD,       Chla_sub*zD
            
            
            #redefine the MLD and euphotic zone in the previous date.            
            Mprev     = MLZ[Day]
            M_EU      = Depth_EU[Day]            
            


    return Pstr, Nutstr, Zstr, I, I_sub, Nd_str, Pstr_sub,  Zstr_sub, Depth_EU, Chla_str, Chla_sub_str, X_ratio




            
            
            
            
            
            
            
            
def two_layered_model_concen_interaction_change_light(Lat, year, initial_conditions, parameters_surf, parameters_sub,AtmAtt,frac_cs):
# This model requires the location, time span, initial conditions which includes the forcing (mixed layer depth), and the parameters
#at the surface layer and subsurface layer
    #===========================================================================================
    #Unpack parameters and define parameters to calculate
    #===========================================================================================
    
    # 1. Unpack initial conditions
    P, Nut, Z, Mprev, MLZ, P_sub, Z_sub, M_EU, Chla, Chla_sub = initial_conditions

    # 2. Unpack parameters
    SolarK, ParFrac, Kdw, Kdp, Vmax, alpha, Ks, Nd, m, Gamma, CN, frac, mup, mug, muz, a,k_e, theta_m = parameters_surf
    alpha_sub, Kdp_sub, Vmax_sub, a_sub, k_e_sub, Gamma_sub, m_sub, CN_sub, X_sub = parameters_sub
    
    # 3. define parameters used in C:CHl model 
        
    C_to_N       = 106/16    # C:N ratio 106:16
    mgC_to_mmolC = 12        # 1mmolC = 12mgC
    #theta_m      = 0.01      # define theta_m for C:CHl ratio calculation
   # X_sub        = 158       # half of time-mean surface X_ratio 
    
    
    #check how many years
    NN=len(year)
    #define initial zero value to calculate the total days (time step) of this simulation
    LL = 0
    for n in range(NN):
        LL += year_days(year[n])
    
    # Initialize arrays 
    Pstr, Nutstr, Zstr, I, Depth_EU, I_sub, Pstr_sub, Nd_str, Zstr_sub, Chla_str, Chla_sub_str, X_ratio= [np.full(LL, np.nan) for _ in range(12)]



    # Loop through each year of year
    Day = -1
    for Yr in range(NN):
        y_day             =  year_days(year[Yr])
        # Loop through the days
        for i in range(y_day):
            Day           += 1
            #=================================================================================
            #
            #                    COMPUTE THE LIGHT ENVIRONMENT
            #
            #=================================================================================
            Kd            = Kdw + Kdp * Chla         # calculate the total light attenuation at the surface layer 
            Depth_EU[Day] = 13.8/Kd                  #calculate euphotic zone

            Kd_sub     = Kdw    + Kdp_sub * Chla_sub # calculate the total light attenuation at the subsurface layer 

            # Compute surface PAR at latitude for times of day and dawn to noon and production rate integration down to MLD
            D1            = 23.45*mt.sin(mt.radians((360.*(284.+i+1)/365.)))                             # Decination = angle of the sun above the equator on each day
            W1            = mt.degrees(mt.acos(-1.*(mt.tan(mt.radians(Lat)) * mt.tan(mt.radians(D1)))))  # Angle(deg) between south (i.e. noon) and setting sun
            
            
            #========================================================================================
            # One-half daylength, hours to noon
            L1            = W1/15.  # Earth rotates 15 = degrees / hour =360/24
            Rx            = 1./mt.sqrt(1.+0.033*np.cos(np.deg2rad((360.*(i+1)/365.)))) # Distance of Earth from sun relative to average, a minor effect
            VtofD         = L1/40.
            TofD          = 12.01-L1-VtofD
          
            # Set initial values for growth rate and light at surface and subsurface layers for each day
            SGr           = 0  #surface growth rate initial value
            SGr_sub       = 0  #subsurface growth rate initial value
            I_d2n         = 0  #surface light initial value
            I_d2n_sub     = 0  #subsurface light initial value 
            cn_sgr_sub    = 40 #time step used to calulate daily light


            
            # Loop over dawn to noon in 40 steps in each day
            for j in range(cn_sgr_sub):
                TofD      =  TofD + VtofD   # for the following see Brock (1981)
                W2        =  (TofD-12.)*15.
                CosZen    = np.sin(np.deg2rad(D1))*np.sin(np.deg2rad(Lat)) \
                          +np.cos(np.deg2rad(D1))*np.cos(np.deg2rad(Lat)) \
                          *np.cos(np.deg2rad(W2))
                Isurf     = SolarK*CosZen/(Rx*Rx)
                Io        = Isurf*AtmAtt[Day]*ParFrac *frac_cs[Day]
                #================================================================================
                #
                #                    Surface layer 
                #
                #=================================================================================
                sm        = 0 #surface layer light initial at each time step of 40 steps
                for k in range(1,int(MLZ[Day])+1):
                    Iz    = Io*np.exp(-1.*Kd*k) #calculate light
                    sm    = sm+Iz #accumulated from surface to MLZ
                    Gr    = (1. - mt.exp(-alpha*Iz/Vmax)) #COMPUTE Phytoplankton Growth Rate for each step from 0 to MLZ and dawn to non             
                    SGr   += Gr #sum the growth rate
                I_d2n     = I_d2n + sm/MLZ[Day] # calculate MLD-averaged irradiance from dawn to noon
                #=================================================================================
                #
                #                   Subsurface layer
                #
                #=================================================================================

                sm_sub       = 0 #subsurface layer initial at each time step of 40 steps
                I_m          = Io*np.exp(-1.*Kd*int(MLZ[Day]))  #light at MLD depth 
                for k2 in range(int(MLZ[Day])+1, int(Depth_EU[Day])+1):
                    Iz2      = I_m*np.exp(-1.*Kd_sub*k2) #subsurface light attenuates from MLD light
                    sm_sub   = sm_sub+Iz2 #accumulated the light from MLD to the euphotic zone
                    Gr_sub   = (1. - mt.exp(-alpha_sub*Iz2/Vmax_sub)) #calculate growth rate
                    SGr_sub  += Gr_sub # sum the growth rate
                I_d2n_sub    = I_d2n_sub+sm_sub/(Depth_EU[Day]-MLZ[Day]) # calculate vertical-averaged irradiance from dawn to noon

            #Out of loop 40: 
            #================================================================================
            #                    Surface layer : averaged light
            #=================================================================================   
        
            I[Day]=2*I_d2n/cn_sgr_sub              # *2 to get dawn to dusk for surface layer light, divided by total time step (40) to get the averaged value

            #=================================================================================
            #                    Subsurface layer : averaged light
            #=================================================================================

            I_sub[Day]=2*I_d2n_sub/cn_sgr_sub      # *2 to get dawn to dusk for subsurface layer light, divided by total time step (40) to get the averaged value
       
            #================================================================================
            #
            #                    Surface layer: growth rate
            #
            #=================================================================================
            # Calculate Phytoplankton Growth Rate over the day (LIGHT EFFECT)
            AveGr      = 2.*Vmax*SGr/(MLZ[Day]*cn_sgr_sub)  # (2* to get dawn to dusk) (divided by MLD and total time steps of 40 to get averaged values)
            # Calculate Phytoplankton Growth rate (NUTRIENT EFFECT)
            NL         = Vmax*Nut/(Ks+Nut)
            # Take the minimum growth rate between light and nutrient growth rate
            G          = min(NL, AveGr)

            #================================================================================
            #
            #                    Subsurface layer: growth rate 
            #
            #=================================================================================  
            # This layer must be limited by light so only calculate the light growth rate
            G_sub= 2.*Vmax_sub*SGr_sub/((Depth_EU[Day]-MLZ[Day]) *cn_sgr_sub)  # (2* to get dawn to dusk) (divided by (euphotic zone-MLD) and total time steps of 40 to get averaged values)    
                
            
            #================================================================================
            #
            #                    Surface layer: zooplankton grazing
            #
            #=================================================================================  
            graz       = a*k_e*(P**2)/(a+k_e*(P**2))
         
            #================================================================================
            #
            #                    Subsurface layer: zooplankton grazing
            #
            #=================================================================================  
            graz_sub   = a_sub*k_e_sub*(P_sub**2)/(a_sub+k_e_sub*(P_sub**2))

            # Calculate MLD entrainment effect on nutrient exchange 
            zeta_deep       = MLZ[Day] - Mprev if MLZ[Day] > Mprev else 0.
            zeta_shallow    = MLZ[Day] - Mprev if MLZ[Day] < Mprev else 0.
            
            #zeta_shallow  =  Mprev - MLZ[Day] if  MLZ[Day] < Mprev else 0.  #zeta and zeta_shallow are always positive 
            #================================================================================
            #
            #                    Surface layer core function 
            #
            #=================================================================================   
            #calculate changes in phytoplankton, nutrient and zooplankton concentrations at surface layer
            
            DP         = G * P - m*P - graz*Z - (MLZ[Day] - Mprev)*P/MLZ[Day] +zeta_shallow*P/MLZ[Day]
            DN         = - G * P + mup*m*P + (1-Gamma-mug) * graz * Z + muz*(CN*(Z**2)) + (frac*MLZ[Day])*(Nd- Nut)/MLZ[Day]- (MLZ[Day] - Mprev)*Nut/MLZ[Day] + zeta_deep*P_sub/MLZ[Day] + zeta_deep*Nd/MLZ[Day] + zeta_shallow*Nut/MLZ[Day]
            DZ         = graz * Gamma * Z - CN*(Z**2)- (MLZ[Day] - Mprev)*Z/MLZ[Day]
           
            
            #================================================================================
            #
            #                    Subsurface layer core function
            #
            #================================================================================= 
            #calculate changes in phytoplankton, nutrient and zooplankton concentrations at the subsurface layer

            DP_sub     = G_sub * P_sub - m_sub * P_sub - graz_sub * Z_sub -((Depth_EU[Day]-MLZ[Day])-(M_EU-Mprev))*P_sub/(Depth_EU[Day]-MLZ[Day]) - zeta_deep*P_sub/(Depth_EU[Day]-MLZ[Day])
            DN_sub     = - G_sub * P_sub +  m_sub * P_sub + (1-Gamma_sub) * graz_sub*Z_sub +CN_sub*(Z_sub**2) -((Depth_EU[Day]-MLZ[Day])-(M_EU-Mprev))*Nd/(Depth_EU[Day]-MLZ[Day])  - zeta_shallow*P/(Depth_EU[Day]-MLZ[Day]) - zeta_deep*Nd/(Depth_EU[Day]-MLZ[Day]) - zeta_shallow*Nut/(Depth_EU[Day]-MLZ[Day])
            DZ_sub     = graz_sub * Gamma_sub * Z_sub - CN_sub*(Z_sub**2) - ((Depth_EU[Day]-MLZ[Day])-(M_EU-Mprev))*Z_sub/(Depth_EU[Day]-MLZ[Day])
            
            #================================================================================= 
            #                  calcualte subsurface state variables
            #================================================================================= 
            P_sub      = P_sub + DP_sub 
            Z_sub      = Z_sub + DZ_sub 
            Nd         = Nd - (frac*MLZ[Day])*(Nd- Nut)/(Depth_EU[Day]-MLZ[Day])+ (1-muz)*CN*(Z**2)*MLZ[Day]/(Depth_EU[Day]-MLZ[Day]) +mug*graz*Z*MLZ[Day]/(Depth_EU[Day]-MLZ[Day]) + (1-mup)*m*P*MLZ[Day]/(Depth_EU[Day]-MLZ[Day]) + DN_sub
 
            
            #================================================================================= 
            #                  calcualte surface state variables
            #================================================================================= 
            P          = P   + DP
            Nut        = Nut + DN
            Z          = Z   + DZ
    

            #================================================================
            #                  calculate surface chla
            #================================================================
            Ik            = Vmax/alpha
            I_star        = I[Day]/Ik
            X             = I_star/(theta_m*(1-np.exp(-I_star)))
            X_ratio[Day]  = X                                  #caluclate C:Chl ratio 
            Chla          = P*(C_to_N)*(1/X)*mgC_to_mmolC      #convert P to chla in mg/m^3

            
            
            #================================================================
            #                  calculate subsurface chla
            #================================================================
            Chla_sub     = P_sub*(C_to_N)*(1/X_sub)*mgC_to_mmolC  #X_sub=158 is half of time-mean surface X_ratio 

            #=================================================================================
            #                   Save state variables into timeseries
            #=================================================================================
            #calcualte the thickness of the subsurface layer 

            
            #calcualte stocks: averaged concentration multiplied by the thickness of each layer
            Pstr[Day],      Nutstr[Day],   Zstr[Day],   Chla_str[Day]        = P, Nut, Z,  Chla
            Pstr_sub[Day],  Zstr_sub[Day], Nd_str[Day], Chla_sub_str[Day]    = P_sub,   Z_sub,     Nd,       Chla_sub
            
            
            #redefine the MLD and euphotic zone in the previous date.            
            Mprev     = MLZ[Day]
            M_EU      = Depth_EU[Day]            
            


    return Pstr, Nutstr, Zstr, I, I_sub, Nd_str, Pstr_sub,  Zstr_sub, Depth_EU, Chla_str, Chla_sub_str, X_ratio



            
            
            
            
            
            
            
            
            
            

            
            
            
            
            