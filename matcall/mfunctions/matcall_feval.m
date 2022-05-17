function varargout = matcall_feval(fh, inputs, issymbol)
    % fh: function handle
    % inputs: cell
    % issymbol: logical array
    % nargout: int
    nargs = length(inputs);

    for i = 1:nargs
        if issymbol{i}
            inputs{i} = eval(inputs{i});
        end
    end

    varargout = fh(inputs{:});
end