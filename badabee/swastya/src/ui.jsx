import { human } from "./format";
export function Badge({ value }) {
  return (
    <span className={`badge ${String(value).toLowerCase()}`}>
      {human(value)}
    </span>
  );
}
export function ErrorBox({ error }) {
  return error ? (
    <p className="error" role="alert">
      {error}
    </p>
  ) : null;
}
