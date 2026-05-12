import { Link } from "react-router-dom";
import { AppRoutes } from "@shared/config/routes";
import { PageHeader } from "@shared/ui";

export function ForbiddenPage() {
  return (
    <div className="page-stack">
      <PageHeader
        description="Your current role does not include the permissions required for this route."
        eyebrow="403"
        title="Access denied"
      />
      <div>
        <Link className="ds-button ds-button--secondary ds-button--md" to={AppRoutes.home}>
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
