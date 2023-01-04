use colored::Colorize;
use tracing::Subscriber;

pub fn relative_path(path: &str) -> String {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    return format!("{}{}{}", manifest_dir, "/", path);
}

struct CustomFormat;

impl<S, N> tracing_subscriber::fmt::FormatEvent<S, N> for CustomFormat
where
    S: Subscriber + for<'a> tracing_subscriber::registry::LookupSpan<'a>,
    N: for<'a> tracing_subscriber::fmt::FormatFields<'a> + 'static,
{
    fn format_event(
        &self,
        context: &tracing_subscriber::fmt::FmtContext<'_, S, N>,
        mut writer: tracing_subscriber::fmt::format::Writer<'_>,
        event: &tracing::Event<'_>,
    ) -> std::fmt::Result {
        // write time
        let time = chrono::Local::now().naive_local();
        let time_str = time.format("%Y-%m-%d %H:%M:%S%.3f").to_string();
        write!(&mut writer, "{} ", time_str.black())?;

        // write level and target
        let metadata = event.metadata();
        write!(
            &mut writer,
            "{:>5} {} ",
            match *metadata.level() {
                tracing::Level::INFO => "INFO".green(),
                tracing::Level::WARN => "WARN".yellow(),
                tracing::Level::ERROR => "ERROR".red(),
                tracing::Level::TRACE => "TRACE".bright_blue(),
                tracing::Level::DEBUG => "DEBUG".bright_black(),
            },
            metadata.target().cyan()
        )?;

        // write all spans
        if let Some(scope) = context.event_scope() {
            let mut spans = scope.from_root().into_iter().peekable();
            // for all spans
            while let Some(span) = spans.next() {
                // write span name
                write!(writer, "{}", span.name().purple())?;

                // get already-formatted fields
                let extensions = span.extensions();
                let fields = &extensions
                    .get::<tracing_subscriber::fmt::FormattedFields<N>>()
                    .expect("cannot get fields");

                // write fields if they exist
                if !fields.is_empty() {
                    // double curly braces = print a single curly brace
                    write!(writer, "{{{}}}", fields)?;
                }

                if spans.peek().is_some() {
                    // there is another span
                    write!(writer, ">")?;
                } else {
                    write!(writer, " ")?;
                }
            }
        }

        // write field using field formatter
        context.field_format().format_fields(writer.by_ref(), event)?;

        // newline
        writeln!(writer)?;

        // success
        Ok(())
    }
}

pub fn setup_tracing() {
    // Configure a custom event formatter
    let format = tracing_subscriber::fmt::format()
        .with_source_location(false)
        .with_target(true)
        .with_timer(tracing_subscriber::fmt::time::SystemTime)
        .compact();

    let my_subscriber = tracing_subscriber::fmt()
        .event_format(CustomFormat)
        .finish();
    tracing::subscriber::set_global_default(my_subscriber).expect("setting tracing default failed");

    tracing::info!("tracing setup done");
}

pub fn api_route(prefix: &str, suffix: &str) -> String {
    format!("{}{}", prefix, suffix)
}
