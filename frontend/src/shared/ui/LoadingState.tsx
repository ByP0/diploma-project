type LoadingStateProps = {
  description?: string;
  title?: string;
};

export function LoadingState({ description = "Preparing the latest data.", title = "Loading" }: LoadingStateProps) {
  return (
    <section className="ds-state ds-state--loading" role="status">
      <span className="ds-loader" aria-hidden="true" />
      <h2>{title}</h2>
      <p>{description}</p>
    </section>
  );
}
