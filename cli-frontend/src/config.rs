use std::path::PathBuf;

use clap::{Args, Parser, Subcommand};
use merge::Merge;

const DEFAULT_URL: &str = "http://localhost:8000";

// take a simple argument
#[derive(Parser, Debug)]
// #[clap(group(ArgGroup::new("config")
//     .args(["config_path", "config_args"])
//     .required(true)))]
pub(crate) struct Arguments {
    #[command(subcommand)]
    pub(crate) command: Command,

    #[arg(short = 'c', long = "config_file")]
    pub(crate) config_file: Option<PathBuf>,

    #[clap(flatten)]
    pub(crate) config_args: Config,
}

#[derive(thiserror::Error, Debug)]
pub(crate) enum ArgError {
    #[error("File IO Error {0:?}")]
    FileIO(#[from] std::io::Error),
    #[error("Deserialization Error {0:?}")]
    Deserialize(#[from] serde_json::Error),
}

impl Arguments {
    pub(crate) fn get_config(&self) -> Result<Config, ArgError> {
        let mut config = Config::default();

        // merge in any config that is stored in the config file
        if let Some(file) = &self.config_file {
            let file_contents = std::fs::read_to_string(&file)?;
            let file_config = serde_json::from_str::<Config>(&file_contents)?;
            config.merge(file_config);
        }

        // merge in any config that is passed as an argument
        config.merge(self.config_args.clone());

        Ok(config)
    }
}

#[derive(Args, Debug, Clone, serde::Serialize, serde::Deserialize, merge::Merge)]
pub(crate) struct Config {
    #[arg(short = 't', long = "token")]
    pub(crate) token: Option<String>,
    #[arg(short = 'u', long = "url")]
    pub(crate) url: Option<String>,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            token: None,
            url: Some(DEFAULT_URL.to_string()),
        }
    }
}

#[derive(Subcommand, Debug)]
pub(crate) enum Command {
    Login { username: String },
    WhoAmI,
    Logout,
}
