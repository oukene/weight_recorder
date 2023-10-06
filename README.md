# weight recorder

This is a home assistant component that allows you to manage your weight records through measured weight.

# installation

step1. You can add it by registering it as a custom repository in HACS, or by downloading the code

step2. Restart HomeAssistant and install the Weight Recorder component.

# How it works

When the value of the sensor selected as the weight entity changes, it finds members of similar weight among the added members and records their weight.

Weight measurement tolerances are entered into member profiles.

If there are more than two people to record weight or there are no subjects, it will be added as unentered data.(When activating the unrecorded data management function in configuration options)

Unrecorded data can be manually added to member profiles

![1.jpg](https://raw.githubusercontent.com/oukene/weight_recorder/main/images/1.jpg)
![2.jpg](https://raw.githubusercontent.com/oukene/weight_recorder/main/images/2.jpg)
![3.jpg](https://raw.githubusercontent.com/oukene/weight_recorder/main/images/3.jpg)
![4.jpg](https://raw.githubusercontent.com/oukene/weight_recorder/main/images/4.jpg)
![5.jpg](https://raw.githubusercontent.com/oukene/weight_recorder/main/images/5.jpg)
![6.jpg](https://raw.githubusercontent.com/oukene/weight_recorder/main/images/6.jpg)



