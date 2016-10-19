unique template features/personality/config_override/config;

"/metadata/features" = append(TEMPLATE);
include { if_exists("personality/"+ PERSONALITY + "/config_override") };
