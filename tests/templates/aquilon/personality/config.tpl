template personality/config;

# Dummy code to generate a compilation error if the function is not defined
# as a parameter
"/system/personality/esp" = create("personality/" + PERSONALITY + "/espinfo");
variable FOO = value("/system/personality/esp/function");
