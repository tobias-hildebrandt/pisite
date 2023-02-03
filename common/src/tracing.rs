use colored::Colorize;
use tracing::field::Visit;
use tracing::Subscriber;
use tracing_subscriber::field::RecordFields;
use tracing_subscriber::fmt::FormatFields;
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
                // span.fields()
                let fields = &extensions
                    .get::<tracing_subscriber::fmt::FormattedFields<N>>()
                    .expect("cannot get fields");

                // write fields if they exist
                if !fields.is_empty() {
                    // double curly braces = print a single curly brace
                    write!(writer, "{{{}}}", fields)?;
                }

                // done with span
                write!(writer, " ")?;
            }
        }

        // write event using field formatter
        context
            .field_format()
            .format_fields(writer.by_ref(), event)?;

        // newline
        writeln!(writer)?;

        // success
        Ok(())
    }
}

impl<'writer> FormatFields<'writer> for CustomFormat {
    fn format_fields<R: RecordFields>(
        &self,
        writer: tracing_subscriber::fmt::format::Writer<'writer>,
        fields: R,
    ) -> std::fmt::Result {
        let mut visitor = FieldVisitor { writer };
        fields.record(&mut visitor);
        visitor.finish()
    }
}

struct FieldVisitor<'writer> {
    writer: tracing_subscriber::fmt::format::Writer<'writer>,
}

impl Visit for FieldVisitor<'_> {
    fn record_debug(&mut self, field: &tracing::field::Field, value: &dyn std::fmt::Debug) {
        if field.name().eq("message") {
            let _ = write!(self.writer, "{:?} ", value);
        } else {
            let _ = write!(self.writer, "{}={:?} ", field.name(), value);
        }
    }

    fn record_str(&mut self, field: &tracing::field::Field, value: &str) {
        if field.name().eq("message") {
            let _ = write!(self.writer, "{} ", value);
        } else {
            let _ = write!(self.writer, "{}={} ", field.name(), value);
        }
    }
}

impl FieldVisitor<'_> {
    fn finish(&mut self) -> std::fmt::Result {
        write!(self.writer, " ")
    }
}

pub fn setup_tracing() {
    let subscriber = tracing_subscriber::fmt()
        .event_format(CustomFormat)
        // .fmt_fields(CustomFormat)
        .finish();
    tracing::subscriber::set_global_default(subscriber).expect("setting global tracer failed");

    tracing::info!("tracing setup done");
}
